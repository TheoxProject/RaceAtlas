from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta, timezone
from threading import Event

import pytest
import test_sync as source
from sqlalchemy import event, insert, select
from sqlalchemy.orm import Session
from test_sync_finalization import coverage
from test_sync_notifications import count, initial

from raceatlas.changes import ChangeError, scope_guards
from raceatlas.models import (
    Account,
    EntryScope,
    ImportWindow,
    Race,
    RaceChange,
    ScopeChange,
    SourceRevision,
)
from raceatlas.notifications import project_notifications
from raceatlas.planning import create_account, put_saved_entry
from raceatlas.sync import service, synchronize


def add_scopes(session, race_id, total):
    existing = list(session.scalars(select(EntryScope.id).where(EntryScope.race_id == race_id)))
    session.execute(
        insert(EntryScope),
        [
            dict(
                id=f"synthetic-{race_id}-{i}",
                race_id=race_id,
                position=i,
                kind="entry_list",
                source_list_id=None,
                identity_status="unverified",
                eligibility_status="unknown",
                raw_label=f"Synthetic scope {i}",
            )
            for i in range(len(existing), total)
        ],
    )
    return existing


@pytest.mark.parametrize("total", [1000, 1001])
def test_final_scope_capacity_is_atomic_and_counts_races_not_subscriptions(
    session, database, total
):
    _, race_id, _ = initial(session, database)
    scopes = add_scopes(session, race_id, total)
    actor = create_account(session, "capacity@example.test")
    actor_id = actor.id
    put_saved_entry(session, actor, scopes[0])  # One subscription never reduces source guards.
    before = coverage(session)["last_successful_sync_at"]
    session.commit()
    now = source.NOW + timedelta(hours=1)
    result = synchronize(database, [source.batch(keys=(), checked=now)], checked_at=now)
    session.expire_all()
    race = session.get(Race, race_id)
    if total == 1000:
        assert result.status == "success" and result.missing_marked == 1
        assert race.source_presence == "to_verify"
        assert count(session, RaceChange) == 1 and count(session, ScopeChange) == 1000
        assert project_notifications(session, session.get(Account, actor_id)).inserted == 1
        assert coverage(session)["status"] == "consistent_sample"
    else:
        assert result.status == "failed" and result.missing_marked == 0
        assert race.source_presence == "present"
        assert race.source.presence_checked_at.astimezone(timezone.utc) == source.NOW
        assert count(session, RaceChange) == count(session, ScopeChange) == 0
        window = session.scalar(select(ImportWindow).where(ImportWindow.run_id == result.run_id))
        assert window.status == "incomplete" and window.diagnostics == ["final_change_capacity"]
        assert coverage(session)["status"] == "incomplete"
        assert coverage(session)["last_successful_sync_at"] == before
    assert count(session, SourceRevision) == 1 and race.revision == 1


def test_large_catalogue_guards_only_real_transitions_not_freshness(session, database, monkeypatch):
    a, b = source.observation("A"), source.observation("B")
    synchronize(database, [source.batch(a, b)], checked_at=source.NOW)
    races = list(session.scalars(select(Race).order_by(Race.id)))
    transition, historical = races
    add_scopes(session, historical.id, 1001)
    historical.source_presence = "to_verify"
    expected = {scope.id for scope in transition.scopes}
    session.commit()
    acquired = []
    original = service.scope_guards

    def guards(session, scopes):
        acquired.append(set(scopes))
        return original(session, scopes)

    monkeypatch.setattr(service, "scope_guards", guards)
    now = source.NOW + timedelta(hours=1)
    result = synchronize(database, [source.batch(keys=(), checked=now)], checked_at=now)
    assert result.status == "success" and result.missing_marked == 1
    assert acquired == [expected]
    later = now + timedelta(hours=1)
    result = synchronize(database, [source.batch(keys=(), checked=later)], checked_at=later)
    session.expire_all()
    assert result.status == "success" and result.missing_marked == 0
    assert acquired == [expected] and count(session, RaceChange) == 1
    assert all(r.source.presence_checked_at.astimezone(timezone.utc) == later for r in races)


def test_second_final_record_failure_rolls_back_entire_final_but_not_committed_business(
    session, database, monkeypatch
):
    a, b, c = (source.observation(key) for key in ("A", "B", "C"))
    synchronize(database, [source.batch(a, b, c)], checked_at=source.NOW)
    before = coverage(session)["last_successful_sync_at"]
    session.commit()
    now = source.NOW + timedelta(hours=1)
    calls = []
    original = service.record_change

    def record(*args, **kwargs):
        value = original(*args, **kwargs)
        if kwargs["kind"] == "presence":
            calls.append(kwargs["race_id"])
            if len(calls) == 2:
                raise ChangeError("Synthetic final failure")
        return value

    monkeypatch.setattr(service, "record_change", record)
    changed = replace(c, name="Committed business window", checked_at=now)
    result = synchronize(database, [source.batch(changed, checked=now)], checked_at=now)
    session.expire_all()
    assert result.status == "partial" and result.missing_marked == 0 and len(calls) == 2
    races = list(session.scalars(select(Race)))
    assert all(r.source_presence == "present" for r in races)
    absent = [r for r in races if r.id in calls]
    assert all(r.source.presence_checked_at.astimezone(timezone.utc) == source.NOW for r in absent)
    assert count(session, RaceChange) == 1 and session.scalar(select(RaceChange.kind)) == "business"
    assert count(session, SourceRevision) == 4
    assert any(r.name == changed.name and r.revision == 2 for r in races)
    assert coverage(session)["status"] == "incomplete"
    assert coverage(session)["last_successful_sync_at"] == before


@pytest.mark.parametrize("save_first", [True, False])
def test_final_commit_linearizes_saved_baseline_without_source_account_lock(
    session, database, save_first
):
    _, _, scopes = initial(session, database)
    actor = create_account(session, "final-subscriber@example.test")
    actor_id = actor.id
    if save_first:
        put_saved_entry(session, actor, scopes[0])
    session.commit()
    recorded, release, waiting = Event(), Event(), Event()
    account_queries = []

    def before(_conn, _cursor, statement, *_args):
        if "FROM account" in statement:
            account_queries.append(1)

    def after(_conn, _cursor, statement, *_args):
        if statement.startswith("INSERT INTO scope_change"):
            recorded.set()
            assert release.wait(5), "Final barrier not released"

    def save():
        with Session(database) as writer:
            actor = writer.get(Account, actor_id)

            def attempting(_conn, _cursor, statement, *_args):
                if "pg_advisory_xact_lock" in statement:
                    waiting.set()

            event.listen(writer.connection(), "before_cursor_execute", attempting)
            entry = put_saved_entry(writer, actor, scopes[0])
            baseline = entry.notifications_after_sequence
            writer.commit()
            return baseline

    event.listen(database, "before_cursor_execute", before)
    event.listen(database, "after_cursor_execute", after)
    now = source.NOW + timedelta(hours=1)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            imported = pool.submit(
                synchronize, database, [source.batch(keys=(), checked=now)], checked_at=now
            )
            try:
                assert recorded.wait(3) and account_queries == []
                saving = None if save_first else pool.submit(save)
                if saving:
                    assert waiting.wait(3) and not saving.done()
            finally:
                release.set()
            assert imported.result(timeout=8).status == "success"
            if saving:
                assert saving.result(timeout=8) == 1
    finally:
        release.set()
        event.remove(database, "before_cursor_execute", before)
        event.remove(database, "after_cursor_execute", after)
    session.expire_all()
    assert project_notifications(session, session.get(Account, actor_id)).inserted == (
        1 if save_first else 0
    )


def test_final_snapshot_is_revalidated_after_real_guard_wait(session, database):
    _, race_id, scopes = initial(session, database)
    session.commit()
    waiting = Event()
    now = source.NOW + timedelta(hours=1)

    def attempting(_conn, _cursor, statement, *_args):
        if "pg_advisory_xact_lock" in statement:
            waiting.set()

    with Session(database) as blocker:
        with scope_guards(blocker, scopes):
            event.listen(database, "before_cursor_execute", attempting)
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    imported = pool.submit(
                        synchronize, database, [source.batch(keys=(), checked=now)], checked_at=now
                    )
                    try:
                        assert waiting.wait(3)
                        # Synthetic guarded server mutation during the wait. Ordinary sync
                        # writers are already excluded by the global import lock.
                        blocker.get(Race, race_id).source_presence = "to_verify"
                        blocker.commit()
                    finally:
                        blocker.rollback()
                    result = imported.result(timeout=8)
            finally:
                event.remove(database, "before_cursor_execute", attempting)
    session.expire_all()
    assert result.status == "failed" and result.missing_marked == 0
    assert count(session, RaceChange) == 0
    assert (
        session.get(Race, race_id).source.presence_checked_at.astimezone(timezone.utc) == source.NOW
    )
    window = session.scalar(select(ImportWindow).where(ImportWindow.run_id == result.run_id))
    assert window.status == "incomplete" and window.diagnostics == ["final_state_changed"]
    assert coverage(session)["status"] == "incomplete"
