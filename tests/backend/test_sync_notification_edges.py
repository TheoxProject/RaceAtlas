from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta, timezone
from threading import Event

import pytest
import test_sync as source
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_sync_notifications import count, initial, subscribe

from raceatlas.changes import scope_guards
from raceatlas.models import (
    Account,
    GeocodeCache,
    ImportItem,
    ImportWindow,
    Race,
    RaceChange,
    ScopeChange,
    SourceRevision,
)
from raceatlas.notifications import project_notifications
from raceatlas.planning import create_account, put_saved_entry
from raceatlas.sync import synchronize
from raceatlas.sync.change_facts import deltas, snapshot
from raceatlas.sync.geocoding import CenterCandidate, OfflineProvider


def test_attested_cancellation_targets_all_scopes_without_presence_invention(session, database):
    observed, race_id, scopes = initial(session, database)
    subscribe(session, scopes)
    now = source.NOW + timedelta(hours=1)
    cancelled = source.observation(html=source.HTML.replace("Programmée", "Annulée"), checked=now)
    assert (
        synchronize(database, [source.batch(cancelled, checked=now)], checked_at=now).status
        == "success"
    )
    session.expire_all()
    assert session.get(Race, race_id).status == "cancelled"
    assert session.get(Race, race_id).source_presence == "present"
    assert session.scalar(select(RaceChange.kind)) == "business"
    assert set(session.scalars(select(ScopeChange.scope_id))) == set(scopes)
    assert all(
        row.payload == {"before": {"status": "scheduled"}, "after": {"status": "cancelled"}}
        for row in session.scalars(select(ScopeChange))
    )


def test_attested_alias_replay_preserves_identity_without_business_notification(session, database):
    observed, race_id, scopes = initial(session, database)
    subscribe(session, scopes)
    now = source.NOW + timedelta(hours=1)
    corrected = source.observation("CORRECTED", season=2028, checked=now)
    proof = source.AliasProof(corrected.key, race_id, observed.key, 1, "synthetic-alias-proof", now)
    for _ in range(2):
        assert (
            synchronize(
                database, [source.batch(corrected, checked=now, aliases=(proof,))], checked_at=now
            ).status
            == "success"
        )
    session.expire_all()
    assert session.get(Race, race_id).source.race_number == "CORRECTED"
    assert tuple(scope.id for scope in session.get(Race, race_id).scopes) == scopes
    assert count(session, RaceChange) == 0 and count(session, SourceRevision) == 1


def test_geocoding_cache_and_center_metadata_are_not_race_deltas(session, database):
    observed = source.observation()
    fact = source.LocationFact(observed.key, "Commune fictive", "26", "location-proof", "26999")
    calls = []

    def lookup(_fact):
        calls.append(1)
        return [CenterCandidate("26999", "Commune fictive", "26", 4.5, 45.0)]

    provider = OfflineProvider("synthetic-center", "v1", lookup)
    synchronize(
        database,
        [source.batch(observed, locations=(fact,))],
        checked_at=source.NOW,
        provider=provider,
    )
    race = session.scalar(select(Race))
    before = snapshot(race)
    race.commune.longitude += 0.001
    race.commune.geocoded_at += timedelta(hours=1)
    assert deltas(before, snapshot(race)) == {}
    session.rollback()
    now = source.NOW + timedelta(days=8)
    refreshed = replace(observed, checked_at=now)
    result = synchronize(
        database,
        [source.batch(refreshed, checked=now, locations=(fact,))],
        checked_at=now,
        provider=provider,
    )
    assert result.status == "success" and len(calls) == 2
    assert count(session, RaceChange) == 0
    assert session.scalar(select(GeocodeCache.checked_at)).astimezone(timezone.utc) == now


def test_real_guard_timeout_rolls_back_before_audit_preserving_prior_window(session, database):
    observed, race_id, scopes = initial(session, database)
    now = source.NOW + timedelta(hours=1)
    changed = replace(observed, name="Must remain unmodified", checked_at=now)
    unrelated = source.observation("INDEPENDENT", checked=now)
    waiting = Event()

    def before(_conn, _cursor, statement, *_args):
        if "pg_advisory_xact_lock" in statement:
            waiting.set()

    with Session(database) as blocker:
        with scope_guards(blocker, scopes):
            event.listen(database, "before_cursor_execute", before)
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        synchronize,
                        database,
                        [source.batch(unrelated, checked=now), source.batch(changed, checked=now)],
                        checked_at=now,
                    )
                    assert waiting.wait(3)
                    result = future.result(timeout=10)
            finally:
                event.remove(database, "before_cursor_execute", before)
                blocker.rollback()
    session.expire_all()
    assert result.status == "partial" and result.missing_marked == 0
    assert count(session, Race) == 2
    assert session.get(Race, race_id).name == observed.name
    windows = list(
        session.scalars(select(ImportWindow).where(ImportWindow.run_id == result.run_id))
    )
    assert sorted(row.status for row in windows) == ["failed", "success"]
    assert next(row for row in windows if row.status == "failed").diagnostics == [
        "change_guard_unavailable"
    ]
    assert count(session, SourceRevision) == 2 and count(session, RaceChange) == 0
    assert list(
        session.scalars(
            select(ImportItem.status).join(ImportWindow).where(ImportWindow.run_id == result.run_id)
        )
    ) == ["created"]


@pytest.mark.parametrize("save_first", [False, True])
def test_real_source_commit_linearizes_subscriptions_with_barriers(session, database, save_first):
    observed, _, scopes = initial(session, database)
    actor = create_account(session, "subscriber@example.test")
    actor_id = actor.id
    if save_first:
        put_saved_entry(session, actor, scopes[0])
    session.commit()
    now = source.NOW + timedelta(hours=1)
    changed = replace(observed, name="Committed scoped update", checked_at=now)
    recorded, release, writer_wait = Event(), Event(), Event()
    account_queries = []

    def before(_conn, _cursor, statement, *_args):
        if "FROM account" in statement:
            account_queries.append(1)

    def after(_conn, _cursor, statement, *_args):
        if statement.startswith("INSERT INTO scope_change"):
            recorded.set()
            if not release.wait(5):
                raise AssertionError("Source commit barrier not released")

    event.listen(database, "before_cursor_execute", before)
    event.listen(database, "after_cursor_execute", after)

    def save_after():
        with Session(database) as writer:
            actor = writer.get(Account, actor_id)

            def attempting(_conn, _cursor, statement, *_args):
                if "pg_advisory_xact_lock" in statement:
                    writer_wait.set()

            event.listen(writer.connection(), "before_cursor_execute", attempting)
            entry = put_saved_entry(writer, actor, scopes[0])
            value = entry.notifications_after_sequence
            writer.commit()
            return value

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            imported = pool.submit(
                synchronize, database, [source.batch(changed, checked=now)], checked_at=now
            )
            try:
                assert recorded.wait(3)
                assert account_queries == []  # No private fanout/Account lookup in the source.
                saving = None if save_first else pool.submit(save_after)
                if saving is not None:
                    assert writer_wait.wait(3) and not saving.done()
            finally:
                release.set()
            assert imported.result(timeout=8).status == "success"
            if saving is not None:
                assert saving.result(timeout=8) == 1
    finally:
        release.set()
        event.remove(database, "before_cursor_execute", before)
        event.remove(database, "after_cursor_execute", after)
    session.expire_all()
    assert project_notifications(session, session.get(Account, actor_id)).inserted == (
        1 if save_first else 0
    )
