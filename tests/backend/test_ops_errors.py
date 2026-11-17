"""One offline operational seam: incomplete source -> honest coverage/private count."""

from dataclasses import replace
from datetime import timedelta

from sqlalchemy import func, select
from test_catalog import request_page, validate
from test_notifications_api import read
from test_private_planning import isolation as isolation
from test_sync import NOW, batch, observation

from raceatlas.models import PersonalNotification, Race, RaceChange, ScopeChange, SourceRecord
from raceatlas.planning import create_account, put_saved_entry
from raceatlas.sync import synchronize


def test_incomplete_detail_preserves_saved_scope_then_real_recovery_notifies_once(
    session, database, app
):
    original = observation("OPS_ERRORS")
    assert synchronize(database, [batch(original)], checked_at=NOW).status == "success"
    race = session.scalar(
        select(Race)
        .join(SourceRecord)
        .where(
            SourceRecord.provider == "ffc",
            SourceRecord.source_season == original.key.season,
            SourceRecord.race_number == original.key.race_number,
        )
    )
    assert race is not None and len(race.scopes) == 2
    expected = next(
        scope for scope in original.scopes if scope.raw_label.startswith("Liste fictive A;")
    )
    followed = next(scope for scope in race.scopes if scope.raw_label == expected.raw_label)
    sibling = next(scope for scope in race.scopes if scope.id != followed.id)
    race_id, followed_id, sibling_id = race.id, followed.id, sibling.id
    actor = create_account(session, "ops-errors@example.test")
    saved = put_saved_entry(session, actor, followed_id, "planned")
    saved_id = saved.id
    session.commit()
    client = app.test_client()
    initial = request_page(client).json
    validate(initial, "RacePage")
    success_at = initial["coverage"]["last_successful_sync_at"]
    assert initial["coverage"]["status"] == "consistent_sample"
    assert read(session, actor)["unread_count"] == 0
    session.commit()

    # Key is announced by the calendar, but its detail is unavailable. No fake
    # HTTP transport/429, absence assertion, PN insertion or cancellation.
    failed_at = NOW + timedelta(hours=1)
    failed = synchronize(
        database, [batch(keys=(original.key,), checked=failed_at)], checked_at=failed_at
    )
    assert failed.status != "success" and failed.missing_marked == 0
    page = request_page(client).json
    validate(page, "RacePage")
    assert page["coverage"]["status"] == "incomplete"
    assert page["coverage"]["last_successful_sync_at"] == success_at
    session.expire_all()
    current = session.get(Race, race_id)
    assert current.source_presence == "present" and current.status == "scheduled"
    assert session.scalar(select(func.count()).select_from(RaceChange)) == 0
    empty = read(session, actor)
    assert empty["unread_count"] == 0 and empty["items"] == []
    session.commit()

    recovered_at = failed_at + timedelta(hours=1)
    recovered = replace(original, name="Synthetic operational recovery", checked_at=recovered_at)
    assert (
        synchronize(
            database, [batch(recovered, checked=recovered_at)], checked_at=recovered_at
        ).status
        == "success"
    )
    coverage = request_page(client).json["coverage"]
    assert coverage["status"] == "consistent_sample"
    assert coverage["last_successful_sync_at"] != success_at
    notifications = read(session, actor)
    assert notifications["unread_count"] == len(notifications["items"]) == 1
    item = notifications["items"][0]
    assert item["scope_id"] == item["entry"]["scope"]["id"] == followed_id
    assert item["entry"]["id"] == saved_id and item["scope_id"] != sibling_id
    assert item["delta"] == {"before": {"name": original.name}, "after": {"name": recovered.name}}
    assert set(session.scalars(select(ScopeChange.scope_id))) == {followed_id, sibling_id}
    assert session.scalar(select(func.count()).select_from(PersonalNotification)) == 0
    session.commit()

    assert (
        synchronize(
            database, [batch(recovered, checked=recovered_at)], checked_at=recovered_at
        ).status
        == "success"
    )
    replay = read(session, actor)
    assert replay["unread_count"] == 1 and replay["items"] == notifications["items"]
    assert session.scalar(select(func.count()).select_from(RaceChange)) == 1
    assert request_page(client).json["coverage"]["status"] == "consistent_sample"
