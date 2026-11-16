from datetime import timedelta, timezone

import pytest
import test_sync as source
from sqlalchemy import event, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from test_sync_finalization import coverage
from test_sync_notifications import count, initial

from raceatlas.models import ImportRun, ImportWindow, Race, RaceChange, ScopeChange, SourceRevision
from raceatlas.sync import service, synchronize


def lost_ack():
    return OperationalError(None, None, RuntimeError("Synthetic commit acknowledgement loss"))


def inject_commit(monkeypatch, *, after, invalidate=False):
    original = Session.commit
    injected = []

    def commit(session):
        terminal = next(
            (
                model
                for model in session.identity_map.values()
                if isinstance(model, ImportRun)
                and model.finished_at is not None
                and model.status in {"success", "partial", "failed"}
            ),
            None,
        )
        if terminal is not None and not injected:
            injected.append((terminal.id, terminal.status, terminal.missing_marked))
            if after:
                original(session)  # The real PG commit, never an after-flush simulation.
            if invalidate:
                session.get_bind().invalidate()
            raise lost_ack()
        return original(session)

    monkeypatch.setattr(Session, "commit", commit)
    return injected


def assert_global_lock_released(database):
    with database.connect() as connection:
        assert connection.scalar(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": service.LOCK_KEY}
        )
        assert connection.scalar(text("SELECT pg_advisory_unlock(:key)"), {"key": service.LOCK_KEY})


@pytest.mark.parametrize(
    "kind,invalidate",
    [("success", False), ("partial", False), ("failed", False), ("success", True)],
)
def test_real_terminal_commit_then_lost_ack_preserves_durable_result(
    session, database, monkeypatch, kind, invalidate
):
    _, race_id, scopes = initial(session, database)
    session.commit()
    injected = inject_commit(monkeypatch, after=True, invalidate=invalidate)
    now = source.NOW + timedelta(hours=1)
    if kind == "success":
        batches = [source.batch(keys=(), checked=now)]
    elif kind == "partial":
        good = source.observation("INDEPENDENT", checked=now)
        missing = source.observation("MISSING", checked=now)
        batches = [source.batch(good, checked=now), source.batch(keys=(missing.key,), checked=now)]
    else:
        batches = []
    reads = []

    def observe(connection, _cursor, statement, *_args):
        if "import_run" in statement and "FOR UPDATE" in statement:
            reads.append(connection.get_isolation_level())

    event.listen(database, "before_cursor_execute", observe)
    try:
        result = synchronize(database, batches, checked_at=now)
    finally:
        event.remove(database, "before_cursor_execute", observe)
    session.expire_all()
    expected_missing = 1 if kind == "success" else 0
    assert injected == [(result.run_id, kind, expected_missing)]
    assert reads == ["READ COMMITTED"]
    assert (result.status, result.missing_marked) == (kind, expected_missing)
    run = session.get(ImportRun, result.run_id)
    assert run.finished_at.astimezone(timezone.utc) == now
    assert (run.status, run.missing_marked) == (kind, expected_missing)
    windows = list(
        session.scalars(select(ImportWindow).where(ImportWindow.run_id == result.run_id))
    )
    assert all("final_commit_error" not in w.diagnostics for w in windows)
    assert session.get(Race, race_id).source_presence == (
        "to_verify" if kind == "success" else "present"
    )
    assert count(session, RaceChange) == (1 if kind == "success" else 0)
    assert count(session, ScopeChange) == (len(scopes) if kind == "success" else 0)
    assert count(session, SourceRevision) == (2 if kind == "partial" else 1)
    assert coverage(session)["status"] == (
        "consistent_sample" if kind == "success" else "incomplete"
    )
    assert_global_lock_released(database)


@pytest.mark.parametrize("phase", ["flush", "commit"])
def test_known_noncommit_rolls_back_before_failure_audit(session, database, monkeypatch, phase):
    _, race_id, _ = initial(session, database)
    previous_success = coverage(session)["last_successful_sync_at"]
    session.commit()
    injected = []

    def before_flush(session, *_args):
        if not injected and any(
            isinstance(row, ImportRun) and row.finished_at is not None for row in session.dirty
        ):
            injected.append(True)
            raise lost_ack()

    if phase == "commit":
        injected = inject_commit(monkeypatch, after=False)
    else:
        event.listen(Session, "before_flush", before_flush)
    now = source.NOW + timedelta(hours=1)
    try:
        result = synchronize(database, [source.batch(keys=(), checked=now)], checked_at=now)
    finally:
        if phase == "flush":
            event.remove(Session, "before_flush", before_flush)
    session.expire_all()
    assert len(injected) == 1 and result.status == "failed" and result.missing_marked == 0
    race = session.get(Race, race_id)
    assert race.source_presence == "present"
    assert race.source.presence_checked_at.astimezone(timezone.utc) == source.NOW
    assert count(session, RaceChange) == count(session, ScopeChange) == 0
    assert count(session, SourceRevision) == 1
    window = session.scalar(select(ImportWindow).where(ImportWindow.run_id == result.run_id))
    assert window.status == "incomplete"
    assert window.diagnostics == ["final_flush_error" if phase == "flush" else "final_commit_error"]
    assert coverage(session)["status"] == "incomplete"
    assert coverage(session)["last_successful_sync_at"] == previous_success
    assert_global_lock_released(database)


def test_failed_local_rollback_invalidates_bound_connection_before_confirmation(
    session, database, monkeypatch
):
    _, race_id, _ = initial(session, database)
    session.commit()
    injected = inject_commit(monkeypatch, after=False)
    original = Session.rollback
    rollback_errors = []

    def rollback(session):
        if injected and not rollback_errors:
            rollback_errors.append(True)
            raise lost_ack()
        return original(session)

    monkeypatch.setattr(Session, "rollback", rollback)
    now = source.NOW + timedelta(hours=1)
    result = synchronize(database, [source.batch(keys=(), checked=now)], checked_at=now)
    session.expire_all()
    assert len(rollback_errors) == 1 and result.status == "failed" and result.missing_marked == 0
    assert session.get(Race, race_id).source_presence == "present"
    assert count(session, RaceChange) == 0
    assert_global_lock_released(database)


@pytest.mark.parametrize("committed", [True, False])
def test_unavailable_confirmation_is_unknown_without_false_audit_even_if_unlock_fails(
    session, database, monkeypatch, committed
):
    _, race_id, _ = initial(session, database)
    session.commit()
    injected = inject_commit(monkeypatch, after=committed)
    failed_reads, failed_unlocks = [], []

    def unavailable(_connection, _cursor, statement, *_args):
        if "import_run" in statement and "FOR UPDATE" in statement:
            failed_reads.append(True)
            raise lost_ack()
        if "pg_advisory_unlock" in statement:
            failed_unlocks.append(True)
            raise lost_ack()

    event.listen(database, "before_cursor_execute", unavailable)
    now = source.NOW + timedelta(hours=1)
    try:
        with pytest.raises(service.FinalizationOutcomeUnknown) as error:
            synchronize(database, [source.batch(keys=(), checked=now)], checked_at=now)
    finally:
        event.remove(database, "before_cursor_execute", unavailable)
    assert error.value.code == "outcome_unknown" and error.value.run_id == injected[0][0]
    assert len(injected) == len(failed_reads) == len(failed_unlocks) == 1
    session.expire_all()
    run = session.get(ImportRun, error.value.run_id)
    assert run.status == ("success" if committed else "running")
    assert run.missing_marked == (1 if committed else 0)
    assert (run.finished_at is not None) == committed
    window = session.scalar(select(ImportWindow).where(ImportWindow.run_id == run.id))
    assert window.status == "success" and window.diagnostics == []
    assert session.get(Race, race_id).source_presence == ("to_verify" if committed else "present")
    assert count(session, RaceChange) == (1 if committed else 0)
    assert_global_lock_released(database)
