from collections import defaultdict
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from raceatlas.ffc import parse_race
from raceatlas.ffc.bootstrap_2027 import _calendar_url, calendar_windows, collect
from raceatlas.ffc.types import DEPARTMENTS, CalendarObservation, SourceKey, WindowRequest


def test_windows_cover_only_civil_year_2027_in_each_department():
    covered = defaultdict(list)
    for window in calendar_windows():
        days = (window.end - window.start).days + 1
        assert 1 <= days <= 14
        covered[window.department].extend(window.start + timedelta(days=i) for i in range(days))
    assert set(covered) == DEPARTMENTS
    for days in covered.values():
        assert days == [date(2027, 1, 1) + timedelta(days=i) for i in range(365)]


def test_collect_deduplicates_detail_after_reading_all_calendars(monkeypatch):
    key = SourceKey(2027, "TEST001")
    detail = "https://competitions.ffc.fr/calendrier/competition/2027/TEST001/fictive/"
    windows = (
        WindowRequest(date(2027, 1, 1), date(2027, 1, 14), "26"),
        WindowRequest(date(2027, 1, 15), date(2027, 1, 28), "26"),
    )
    fetched = []

    class Fetcher:
        def get(self, url, media_type):
            fetched.append((url, media_type))
            return "<html></html>"

    def calendar(html, *, requested, source_url, checked_at):
        return (
            CalendarObservation(
                source_url,
                checked_at,
                requested,
                requested.start,
                requested.end,
                requested.department,
                1,
                (key,),
                "consistent_sample",
                (),
            ),
            {key: detail},
        )

    def race(html, *, source_url, checked_at, expected_key, expected_department):
        fixture = Path(__file__).resolve().parents[2] / "fixtures/ffc/race.synthetic.html"
        observation = parse_race(
            fixture.read_text(encoding="utf-8"), source_url=source_url, checked_at=checked_at
        )
        return replace(
            observation, start_date=date(2027, 1, 14), end_date=date(2027, 1, 15)
        ), "Ville fictive"

    monkeypatch.setattr("raceatlas.ffc.bootstrap_2027.parse_public_calendar", calendar)
    monkeypatch.setattr("raceatlas.ffc.bootstrap_2027.parse_public_race", race)
    batches, scope = collect(Fetcher(), windows)
    assert fetched == [
        (_calendar_url(windows[0]), "text/html"),
        (_calendar_url(windows[1]), "text/html"),
        (detail, "text/html"),
    ]
    assert scope["parsed_races"] == 1
    assert all(batch.details[0].checked_at >= batch.calendar.checked_at for batch in batches)
    assert all(batch.locations[0].commune_name == "Ville fictive" for batch in batches)
