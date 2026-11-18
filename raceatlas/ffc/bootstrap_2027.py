"""One-time collection of positive 2027 observations for an authorized operator."""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from itertools import pairwise
from time import monotonic, sleep
from urllib.parse import urlencode, urlsplit

import requests
from sqlalchemy import create_engine, func, select

from raceatlas.config import database_url
from raceatlas.models import ImportItem, ImportWindow, Race
from raceatlas.sync import DetailFailure, LocationFact, WindowBatch
from raceatlas.sync.geocoding import OfflineProvider
from raceatlas.sync.service import bootstrap_catalog_2027

from .public_2027 import parse_public_calendar, parse_public_race
from .types import DEPARTMENTS, AdapterError, WindowRequest

CALENDAR_URL = "https://competitions.ffc.fr/calendrier/"
START, END = date(2027, 1, 1), date(2028, 1, 1)
MAX_BYTES = 2 * 1024 * 1024
REQUEST_INTERVAL = 1.5


class CollectionError(RuntimeError):
    """Sanitized operator error."""


class Fetcher:
    def __init__(self, session):
        self.session = session
        self.next_request = 0.0

    def get(self, url, media_type):
        delay = self.next_request - monotonic()
        if delay > 0:
            sleep(delay)
        try:
            with self.session.get(
                url, timeout=(5, 15), stream=True, allow_redirects=False
            ) as response:
                if response.status_code in {404, 410}:
                    return None
                if response.status_code != 200:
                    raise CollectionError(f"Provider returned HTTP {response.status_code}.")
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
                if content_type != media_type:
                    raise CollectionError("Provider returned an unexpected content type.")
                parts = bytearray()
                deadline = monotonic() + 25
                for chunk in response.iter_content(chunk_size=16384):
                    if monotonic() > deadline or len(parts) + len(chunk) > MAX_BYTES:
                        raise CollectionError("Provider exceeded the response limits.")
                    parts.extend(chunk)
                return parts.decode("utf-8-sig")
        except (requests.RequestException, UnicodeError):
            raise CollectionError("Provider request or response decoding failed.") from None
        finally:
            self.next_request = monotonic() + REQUEST_INTERVAL


def calendar_windows():
    boundaries = tuple(START + timedelta(days=days) for days in range(0, 365, 14)) + (END,)
    return (
        WindowRequest(start, limit - timedelta(days=1), department)
        for department in sorted(DEPARTMENTS)
        for start, limit in pairwise(boundaries)
    )


def _calendar_url(window):
    params = urlencode(
        {
            "departement": window.department,
            "debut": window.start.isoformat(),
            "nbjours": (window.end - window.start).days + 1,
        }
    )
    return f"{CALENDAR_URL}?{params}"


def _expected_detail_url(url, key):
    parsed = urlsplit(url)
    path = rf"/calendrier/competition/{key.season}/{re.escape(key.race_number)}/[A-Za-z0-9-]+/"
    return (
        parsed.scheme == "https"
        and parsed.netloc == "competitions.ffc.fr"
        and re.fullmatch(path, parsed.path)
        and not (parsed.query or parsed.fragment)
    )


def collect(fetcher, windows, progress=lambda *_: None):
    scope = Counter()
    calendars, memberships = [], defaultdict(set)
    for window in windows:
        scope["requested_windows"] += 1
        url = _calendar_url(window)
        body = fetcher.get(url, "text/html")
        if body is None:
            scope["missing_calendar"] += 1
            continue
        checked_at = datetime.now(timezone.utc)
        try:
            calendar, links = parse_public_calendar(
                body, source_url=url, requested=window, checked_at=checked_at
            )
        except AdapterError as error:
            scope[f"calendar_{error.diagnostic.code}"] += 1
            continue
        calendars.append(calendar)
        if calendar.status != "consistent_sample":
            scope["incoherent_calendar"] += 1
            continue
        scope["consistent_windows"] += 1
        for key, detail_url in links.items():
            memberships[key].add((window.department, detail_url))
        if scope["requested_windows"] % 27 == 0:
            progress("Calendriers contrôlés", scope["requested_windows"])

    observations, failures = {}, {}
    for key, matches in memberships.items():
        if len(matches) != 1:
            failures[key] = "conflicting_detail_links"
            continue
        department, url = next(iter(matches))
        if not _expected_detail_url(url, key):
            failures[key] = "invalid_detail_link"
            continue
        body = fetcher.get(url, "text/html")
        if body is None:
            failures[key] = "missing_detail"
            continue
        try:
            observation, commune = parse_public_race(
                body,
                source_url=url,
                checked_at=datetime.now(timezone.utc),
                expected_key=key,
                expected_department=department,
            )
        except AdapterError as error:
            failures[key] = error.diagnostic.code
            continue
        if not START <= observation.start_date < END:
            failures[key] = "outside_civil_year"
            continue
        observations[key] = (observation, commune)

    scope.update(failures.values())
    scope["distinct_detail_candidates"] = len(memberships)
    scope["parsed_races"] = len(observations)
    for observation, commune in observations.values():
        scope[f"discipline_{observation.discipline}"] += 1
        if commune:
            scope["explicit_communes"] += 1

    batches = []
    for calendar in calendars:
        if calendar.status != "consistent_sample":
            batches.append(WindowBatch(calendar, ()))
            continue
        details, locations, window_failures = [], [], []
        for key in calendar.keys:
            result = observations.get(key)
            if result is None:
                window_failures.append(DetailFailure(key, failures.get(key, "missing_detail")))
                continue
            observation, commune = result
            details.append(observation)
            if commune:
                locations.append(LocationFact(key, commune, observation.department, "ffc-commune"))
        batches.append(
            WindowBatch(calendar, tuple(details), tuple(locations), failures=tuple(window_failures))
        )
    return tuple(batches), scope


def _stored_summary(engine, run_id):
    with engine.connect() as connection:
        items = dict(
            connection.execute(
                select(ImportItem.status, func.count())
                .join(ImportWindow)
                .where(ImportWindow.run_id == run_id)
                .group_by(ImportItem.status)
            ).all()
        )
        accepted_races = (
            select(ImportItem.race_id)
            .join(ImportWindow)
            .where(
                ImportWindow.run_id == run_id,
                ImportItem.status.in_(("created", "updated", "unchanged")),
            )
        )
        races = connection.execute(
            select(func.count(), func.count(Race.commune_id)).where(Race.id.in_(accepted_races))
        ).one()
    return {"items": items, "accepted_races": races[0], "located_races": races[1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expect-host")
    parser.add_argument("--expect-database")
    args = parser.parse_args()
    if args.apply and not (args.expect_host and args.expect_database):
        parser.error("--apply requires the expected database host and name")

    with requests.Session() as session:
        session.trust_env = False
        session.headers["User-Agent"] = "RaceAtlas/1.0 (one-time 2027 calendar import)"
        fetcher = Fetcher(session)
        try:
            batches, scope = collect(
                fetcher,
                calendar_windows(),
                lambda *parts: print(*parts, file=sys.stderr, flush=True),
            )
            print(json.dumps(dict(scope), sort_keys=True), flush=True)
            if not scope["parsed_races"]:
                raise CollectionError("No verified 2027 race was collected.")
            if not args.apply:
                return 0
        except CollectionError as error:
            print(error, file=sys.stderr)
            return 2

    engine = create_engine(database_url(), pool_pre_ping=True, connect_args={"connect_timeout": 10})
    try:
        result = bootstrap_catalog_2027(
            engine,
            batches,
            target_host=args.expect_host,
            target_database=args.expect_database,
            provider=OfflineProvider("no-commune-center-source", "1", lambda _: ()),
        )
        summary = _stored_summary(engine, result.run_id)
        print(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "status": result.status,
                    "missing_marked": result.missing_marked,
                    **summary,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return 0 if result.status == "partial" and summary["accepted_races"] else 2
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
