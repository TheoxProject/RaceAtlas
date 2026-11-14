import copy
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, UUID

import pytest
from icalendar import Calendar

from raceatlas.planning_ics import (
    EventMetadata,
    event_payloads,
    event_uid,
    render_calendar,
)
from raceatlas.planning_snapshot import PlanningLimitError, PlanningLimits

LIMITS = PlanningLimits()
STAMP = datetime(2026, 11, 14, 8, 0, tzinfo=timezone.utc)


@pytest.fixture
def item():
    catalog = json.loads(
        (Path(__file__).parents[2] / "fixtures/catalog.v1.json").read_text(encoding="utf-8")
    )
    race = copy.deepcopy(catalog["races"][0])
    scope = race.pop("entry_scopes")[0]
    return dict(id="saved-one", scope_id=scope["id"], status="planned", race=race, scope=scope)


def encode(items, account="account-one", limits=LIMITS):
    events = event_payloads(items, account, limits)
    return render_calendar(events, {p.scope_id: EventMetadata(STAMP, 0) for p in events}, limits)


def events(data):
    calendar = Calendar.from_ical(data)
    assert calendar.errors == []
    return [component for component in calendar.walk() if component.name == "VEVENT"]


@pytest.mark.parametrize(
    "start,end,exclusive",
    [
        ("2026-12-31", "2027-01-02", date(2027, 1, 3)),
        ("2024-02-28", "2024-02-29", date(2024, 3, 1)),
        ("2026-03-29", "2026-03-29", date(2026, 3, 30)),
        ("2026-10-25", "2026-10-25", date(2026, 10, 26)),
        ("0001-01-01", "0001-01-01", date(1, 1, 2)),
    ],
)
def test_all_day_parser_and_exclusive_end_not_timezone_dependent(
    item, start, end, exclusive, monkeypatch
):
    item["race"].update(start_date=start, end_date=end)
    outputs = []
    for zone in ("UTC", "Pacific/Honolulu", "Europe/Paris"):
        monkeypatch.setenv("TZ", zone)
        outputs.append(encode([item]))
    assert outputs[0] == outputs[1] == outputs[2]
    value = events(outputs[0])[0]
    assert value["DTSTART"].dt == date.fromisoformat(start)
    assert value["DTEND"].dt == exclusive
    assert value["DTSTART"].params == {"VALUE": "DATE"}
    assert value["DTSTAMP"].dt == STAMP and int(value["SEQUENCE"]) == 0
    assert not value["DTSTART"].params.get("TZID")


@pytest.mark.parametrize(
    "start,end",
    [
        ("2025-02-29", "2025-03-01"),
        ("2026-11-02", "2026-11-01"),
        ("9999-12-31", "9999-12-31"),
        ("20260101", "2026-01-02"),
        ("not-a-date", "2026-01-02"),
    ],
)
def test_invalid_dates_refused_without_wrap(item, start, end):
    item["race"].update(start_date=start, end_date=end)
    with pytest.raises(PlanningLimitError):
        encode([item])


def test_utf8_folding_escape_and_no_component_or_property_injection(item):
    title = "é😀" * 60 + "\\,;\r\nBEGIN:VEVENT\nATTENDEE:mailto:fake@example.test\rEND:VEVENT"
    item["race"]["name"] = title
    data = encode([item])
    assert data.endswith(b"\r\n") and b"\n" not in data.replace(b"\r\n", b"")
    assert all(len(line) <= 75 for line in data.split(b"\r\n"))
    for line in data.split(b"\r\n"):
        line.decode("utf-8")
    parsed = events(data)
    assert len(parsed) == 1
    assert (
        str(parsed[0]["SUMMARY"])
        == title.replace("\r\n", "\n").replace("\r", "\n") + " — " + item["scope"]["raw_label"]
    )
    assert set(parsed[0]) == {
        "UID",
        "DTSTART",
        "DTEND",
        "SUMMARY",
        "DESCRIPTION",
        "LOCATION",
        "DTSTAMP",
        "SEQUENCE",
    }
    assert set(Calendar.from_ical(data)) == {"VERSION", "PRODID"}


def test_empty_201_and_scopes_same_race_are_distinct(item):
    assert events(encode([])) == []
    items = []
    for index in range(201):
        other = copy.deepcopy(item)
        other["id"] = "saved-" + str(index)
        other["scope_id"] = other["scope"]["id"] = "scope-" + str(index)
        items.append(other)
    parsed = events(encode(items))
    assert len(parsed) == 201 and len({str(value["UID"]) for value in parsed}) == 201


def _independent_uuid5(namespace, name):
    raw = bytearray(hashlib.sha1(namespace.bytes + name.encode("utf-8")).digest()[:16])
    raw[6] = raw[6] & 15 | 80
    raw[8] = raw[8] & 63 | 128
    return UUID(bytes=bytes(raw))


def test_uid_exact_namespace_tuple_and_not_host_incarnation_or_email(item):
    namespace = _independent_uuid5(
        NAMESPACE_URL, "https://github.com/TheoxProject/RaceAtlas/private-calendar/v1"
    )
    expected = str(_independent_uuid5(namespace, '["v1","account-one","scope-é"]'))
    assert event_uid("account-one", "scope-é") == expected
    assert expected != event_uid("account-two", "scope-é")
    assert expected != event_uid("account-one", "scope-e")
    before = event_payloads([item], "account-one", LIMITS)[0]
    item["id"] = "new-incarnation"
    item["race"]["source"]["checked_at"] = "2040-01-01T00:00:00Z"
    after = event_payloads([item], "account-one", LIMITS)[0]
    assert before.properties == after.properties and before.fingerprint != after.fingerprint


def test_uncertainty_registered_cancellation_and_no_invented_coordinates(item):
    item["race"]["location"] = None
    item["race"]["source_presence"] = "to_verify"
    item["status"] = "registered"
    value = events(encode([item]))[0]
    assert "non localisé" in str(value["LOCATION"])
    assert "non vérifié" in str(value["DESCRIPTION"]) and "to_verify" in str(value["DESCRIPTION"])
    assert "STATUS" not in value and "GEO" not in value
    item["race"]["status"] = "cancelled"
    assert str(events(encode([item]))[0]["STATUS"]) == "CANCELLED"


def test_freshness_rule_order_and_admin_revision_are_not_export_content(item):
    first = event_payloads([item], "account-one", LIMITS)[0]
    item["race"]["revision"] = 92
    item["revision"] = 92
    item["race"]["source"]["checked_at"] = "2040-01-01T00:00:00Z"
    item["scope"]["rules"].reverse()
    for rule in item["scope"]["rules"]:
        rule["category_codes"].reverse()
    assert event_payloads([item], "account-one", LIMITS)[0] == first


@pytest.mark.parametrize("kind", ["events", "response", "text", "invalid_unicode", "control"])
def test_exact_output_limits_and_invalid_text(item, kind):
    limits = LIMITS
    if kind == "events":
        items = [item, copy.deepcopy(item)]
        limits = replace(limits, events=1)
    else:
        items = [item]
        if kind == "response":
            limits = replace(limits, response_bytes=100)
        if kind == "text":
            item["race"]["name"] = "é" * 8193
        if kind == "invalid_unicode":
            item["race"]["name"] = "\ud800"
        if kind == "control":
            item["race"]["name"] = "hello\x00world"
    with pytest.raises(PlanningLimitError):
        encode(items, limits=limits)


def test_excluded_unrepresentable_item_does_not_invalidate_export(item):
    item["status"] = "interested"
    item["race"].update(name="\ud800", end_date="9999-12-31")
    assert events(encode([item])) == []


def test_new_process_restart_host_and_timezone_do_not_change_uid_or_bytes(item):
    script = """
import json, sys
from datetime import datetime, timezone
from raceatlas.planning_ics import event_payloads, render_calendar, EventMetadata
from raceatlas.planning_snapshot import PlanningLimits
item=json.load(sys.stdin)
limits=PlanningLimits()
parts=event_payloads([item], 'account-one', limits)
metadata={
    part.scope_id:EventMetadata(datetime(2026,11,14,8,tzinfo=timezone.utc),0)
    for part in parts
}
sys.stdout.buffer.write(render_calendar(parts,metadata,limits))
"""
    outputs = []
    for host, zone, seed in (
        ("https://site-one.example.test", "UTC", "17"),
        ("https://site-two.example.test", "Pacific/Honolulu", "29"),
    ):
        environment = {**os.environ, "APP_BASE_URL": host, "TZ": zone, "PYTHONHASHSEED": seed}
        result = subprocess.run(
            [sys.executable, "-c", script],
            input=json.dumps(item, ensure_ascii=False).encode("utf-8"),
            capture_output=True,
            env=environment,
            timeout=10,
            check=True,
        )
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1] == encode([item])
