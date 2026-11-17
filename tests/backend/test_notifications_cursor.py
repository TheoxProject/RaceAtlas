import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from sqlalchemy import event, insert
from test_notifications import PROVENANCE
from test_notifications_api import KEY, read
from test_notifications_http import BASE
from test_private_planning import ORIGIN, actor_client
from test_private_planning import app as _planning_app
from test_private_planning import isolation as isolation

from raceatlas.models import Account, EntryScope, RaceChange, ScopeChange
from raceatlas.notifications_api import (
    NotificationQueryError,
    _cursor,
    parse_query,
    read_notifications,
)
from raceatlas.planning import put_saved_entry
from raceatlas.serialization import timestamp


@pytest.fixture
def app(database):
    yield from _planning_app.__wrapped__(database)


def b64(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def signed(key, actor_id, raw):
    body = b64(raw)
    message = b"notifications-cursor:v1\0" + actor_id.encode() + b"\0" + body.encode("ascii")
    return body + "." + b64(hmac.new(key, message, hashlib.sha256).digest())


@pytest.mark.parametrize("character", ["\U0010ffff", "\x01"])
def test_compact_cursor_bound_for_both_maximum_ids_and_timestamp(character):
    at = datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
    opaque = character * 64
    cursor = _cursor(KEY, "actor", at, opaque, opaque)
    assert len(cursor) <= 768 < 1024
    if len(character.encode("utf-8")) == 4:
        assert len(cursor) == 768
    assert parse_query(1, cursor)[1][:3] == (at, opaque, opaque)


def maximum_ids(session, actor, character):
    scope_id = character * 64
    newer_id, older_id = character * 64, character * 63 + "x"
    at = datetime(2026, 11, 17, 8, 0, 0, 123456, tzinfo=timezone.utc)
    session.add(
        EntryScope(
            id=scope_id,
            race_id="race-road-split",
            position=99,
            kind="entry_list",
            source_list_id=None,
            identity_status="unverified",
            eligibility_status="unknown",
            raw_label="Synthetic opaque scope",
        )
    )
    session.flush()
    put_saved_entry(session, actor, scope_id)
    session.execute(
        insert(RaceChange),
        [
            dict(
                id=change_id,
                race_id="race-road-split",
                event_key=f"cursor-{index}",
                kind="business",
                signature="0" * 64,
                provenance=PROVENANCE,
                created_at=at - timedelta(seconds=index),
            )
            for index, change_id in enumerate([newer_id, older_id])
        ],
    )
    session.execute(
        insert(ScopeChange),
        [
            dict(
                change_id=change_id,
                scope_id=scope_id,
                sequence=index + 1,
                payload={"before": {"name": "Before"}, "after": {"name": "After"}},
            )
            for index, change_id in enumerate([newer_id, older_id])
        ],
    )
    session.commit()
    return newer_id, older_id, scope_id


def validate_document(document, schema_name="notifications.schema.json", fragment=""):
    root = Path(__file__).resolve().parents[2] / "contracts"
    registry = Registry()
    for name in ["notifications.schema.json", "planning.schema.json"]:
        path = root / name
        registry = registry.with_resource(
            path.as_uri(), Resource.from_contents(json.loads(path.read_text(encoding="utf-8")))
        )
    Draft202012Validator(
        {"$ref": (root / schema_name).as_uri() + fragment},
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(document)


@pytest.mark.parametrize("character", ["\U0001f6b4", "\x01"])
def test_both_maximum_ids_roundtrip_real_service_and_http_page_two(
    app, database, seeded, character
):
    client, actor_id = actor_client(app, database)
    actor = seeded.get(Account, actor_id)
    newer, older, scope_id = maximum_ids(seeded, actor, character)
    first = read(seeded, actor, limit=1)
    assert first["has_more"] and len(first["next_cursor"]) <= 768
    second = read(seeded, actor, limit=1, cursor=first["next_cursor"])
    for page, expected in [(first, newer), (second, older)]:
        validate_document(page)
        assert page["unread_count"] == 2 and len(page["items"]) == 1
        assert page["items"][0]["change_id"] == expected
        assert page["items"][0]["scope_id"] == page["items"][0]["entry"]["scope"]["id"] == scope_id
    assert not second["has_more"] and second["next_cursor"] is None
    seeded.commit()  # Release the service's Account lock before another HTTP Session.
    http_first = client.get(BASE, query_string={"limit": 1}, base_url=ORIGIN)
    assert http_first.status_code == 200
    assert len(http_first.json["next_cursor"]) <= 768
    http_second = client.get(
        BASE, query_string={"limit": 1, "cursor": http_first.json["next_cursor"]}, base_url=ORIGIN
    )
    assert http_second.status_code == 200
    validate_document(http_first.json)
    validate_document(http_second.json)
    assert http_first.json["unread_count"] == http_second.json["unread_count"] == 2
    assert http_second.json["items"][0]["change_id"] == older
    assert http_second.json["items"][0]["scope_id"] == scope_id
    saved = client.get("/api/v1/me/saved-entries", base_url=ORIGIN)
    assert saved.status_code == 200 and len(saved.json["items"]) == 1
    validate_document(saved.json, "planning.schema.json", "#/$defs/SavedList")
    assert saved.json["items"][0]["scope_id"] == saved.json["items"][0]["scope"]["id"] == scope_id


def test_legacy_json_v1_cursor_still_reads_page_two(app, database, seeded):
    client, actor_id = actor_client(app, database)
    actor = seeded.get(Account, actor_id)
    _, older, _ = maximum_ids(seeded, actor, "a")
    first = read(seeded, actor, limit=1)
    claim = parse_query(1, first["next_cursor"])[1]
    raw = json.dumps([1, timestamp(claim[0]), claim[1], claim[2]], separators=(",", ":")).encode()
    legacy = signed(KEY, actor_id, raw)
    assert read(seeded, actor, limit=1, cursor=legacy)["items"][0]["change_id"] == older
    seeded.commit()  # Caller owns this service read transaction too.
    legacy_http = signed(app.extensions["auth"].settings.csrf_key, actor_id, raw)
    response = client.get(BASE, query_string={"limit": 1, "cursor": legacy_http}, base_url=ORIGIN)
    assert response.status_code == 200 and response.json["items"][0]["change_id"] == older


def test_malformed_compact_payloads_fail_before_any_sql(seeded):
    from raceatlas.planning import create_account

    actor = create_account(seeded, "malformed@example.test")
    actor_id = actor.id
    seeded.commit()
    date = b"2026-11-17T08:00:00.123456Z"
    invalid = [
        b"3\0" + date + b"\0change\0scope",  # unknown binary version
        b"2\0" + date + b"\0change",  # missing separator/field
        b"2\0" + date + b"\0change\0scope\0extra",  # extra separator, including an ID NUL
        b"2\0" + date + b"\0\xff\0scope",  # malformed UTF-8
        b"2\0bad-date\0change\0scope",
        b"2\0" + date[:-1] + b"\0change\0scope",  # no timezone
        b"2\0" + date + b"\0\0scope",  # empty ID
        b"2\0" + date + b"\0" + b"x" * 65 + b"\0scope",  # oversized ID
        b'[2,"2026-11-17T08:00:00Z","change","scope"]',  # not a v1 legacy cursor
    ]
    statements = []

    def observe(*_args):
        statements.append(True)

    event.listen(seeded.bind, "before_cursor_execute", observe)
    try:
        for raw in invalid:
            with pytest.raises(NotificationQueryError):
                read_notifications(seeded, actor, cursor_key=KEY, cursor=signed(KEY, actor_id, raw))
        assert statements == []
    finally:
        event.remove(seeded.bind, "before_cursor_execute", observe)
