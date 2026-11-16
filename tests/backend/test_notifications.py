from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, insert, select, text
from sqlalchemy.exc import IntegrityError, SAWarning
from sqlalchemy.orm import Session

from raceatlas.changes import ChangeError, record_change, scope_guards
from raceatlas.models import (
    Account,
    CatalogState,
    PersonalCalendarEventStore,
    PersonalNotification,
    RaceChange,
    SavedEntry,
    ScopeChange,
)
from raceatlas.notifications import project_notifications
from raceatlas.planning import (
    create_account,
    delete_account,
    delete_saved_entry,
    put_saved_entry,
    update_saved_entry,
)

ONE, TWO = "scope-split-one", "scope-split-two"
PROVENANCE = {
    "source_url": "https://example.test/synthetic",
    "checked_at": "2026-11-15T12:00:00+00:00",
    "normalization_version": "1.0.0",
}


def change(
    session, key="mutation-1", scopes=(ONE, TWO), before="Before", after="After", guard=None
):
    values = dict(
        race_id="race-road-split",
        event_key=key,
        kind="business",
        targets={scope: {"before": {"name": before}, "after": {"name": after}} for scope in scopes},
        provenance=PROVENANCE,
    )
    if guard is not None:
        return record_change(session, guard, **values)
    with scope_guards(session, scopes) as locked:
        return record_change(session, locked, **values)


def users(session):
    return create_account(session, "alice@example.test"), create_account(
        session, "bob@example.test"
    )


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


@pytest.mark.parametrize("status", ["interested", "planned", "registered", "completed"])
def test_projection_status_idempotence_scopes_and_epoch(seeded, status):
    alice, bob = users(seeded)
    original = seeded.execute(select(CatalogState.epoch, CatalogState.revision)).one()
    first = put_saved_entry(seeded, alice, ONE, status)
    put_saved_entry(seeded, alice, TWO, status)
    put_saved_entry(seeded, bob, TWO, "interested")
    before = (first.id, first.updated_at, first.revision, first.notifications_after_sequence)
    change_id = change(seeded)
    assert change(seeded) == change_id
    assert count(seeded, RaceChange) == 1
    result = project_notifications(seeded, alice, batch_size=1)
    assert (result.inserted, result.pending) == (1, True)
    assert project_notifications(seeded, alice).inserted == 1
    assert project_notifications(seeded, alice).inserted == 0
    assert project_notifications(seeded, bob).inserted == 1
    same = put_saved_entry(seeded, alice, ONE, status)
    assert (same.id, same.updated_at, same.revision, same.notifications_after_sequence) == before
    update_saved_entry(seeded, alice, first.id, "completed" if status != "completed" else "planned")
    assert (first.id, first.notifications_after_sequence) == (before[0], before[3])
    assert seeded.execute(select(CatalogState.epoch, CatalogState.revision)).one() == original


def test_record_keys_are_mutation_incarnations_and_noop_has_no_event(seeded):
    assert change(seeded, before="A", after="A") is None
    ids = [
        change(seeded, "step-1", before="A", after="B"),
        change(seeded, "step-2", before="B", after="A"),
        change(seeded, "step-3", before="A", after="B"),
    ]
    assert len(set(ids)) == 3
    assert list(
        seeded.scalars(
            select(ScopeChange.sequence)
            .where(ScopeChange.scope_id == ONE)
            .order_by(ScopeChange.sequence)
        )
    ) == [1, 2, 3]
    with pytest.raises(ChangeError, match="conflict"):
        change(seeded, "step-1", before="A", after="different")
    assert count(seeded, RaceChange) == 3


def test_remove_and_account_cascade_exact_scope_preserve_ics(seeded):
    alice, bob = users(seeded)
    one = put_saved_entry(seeded, alice, ONE)
    put_saved_entry(seeded, alice, TWO)
    put_saved_entry(seeded, bob, ONE)
    seeded.add(
        PersonalCalendarEventStore(
            account_id=alice.id,
            scope_id=ONE,
            fingerprint="a" * 64,
            stamp=datetime.now(timezone.utc),
            sequence=0,
        )
    )
    change(seeded)
    project_notifications(seeded, alice)
    project_notifications(seeded, bob)
    delete_saved_entry(seeded, alice, one.id)
    assert {(n.account_id, n.scope_id) for n in seeded.scalars(select(PersonalNotification))} == {
        (alice.id, TWO),
        (bob.id, ONE),
    }
    assert seeded.get(PersonalCalendarEventStore, (alice.id, ONE)) is not None
    new = put_saved_entry(seeded, alice, ONE)
    assert new.id != one.id and new.notifications_after_sequence == 1
    assert project_notifications(seeded, alice).inserted == 0
    delete_account(seeded, alice)
    assert count(seeded, PersonalNotification) == 1
    assert seeded.scalar(select(PersonalNotification.account_id)) == bob.id


@pytest.mark.parametrize("bad_pair", ["subscription", "change"])
def test_composite_fks_refuse_crossed_pairs(seeded, bad_pair):
    alice, _ = users(seeded)
    put_saved_entry(seeded, alice, ONE)
    put_saved_entry(seeded, alice, TWO)
    recorded = change(seeded, scopes=(ONE,))
    if bad_pair == "subscription":
        delete_saved_entry(
            seeded, alice, seeded.scalar(select(SavedEntry.id).where(SavedEntry.scope_id == TWO))
        )
    with pytest.raises(IntegrityError) as failed:
        with seeded.begin_nested():
            seeded.add(PersonalNotification(account_id=alice.id, change_id=recorded, scope_id=TWO))
            seeded.flush()
    assert failed.value.orig.sqlstate == "23503"
    assert count(seeded, PersonalNotification) == 0


def test_guard_outer_and_nested_rollback_lifetime(seeded):
    with scope_guards(seeded, [TWO, ONE, ONE]) as outer:
        assert outer.scope_ids == (ONE, TWO)
        with pytest.raises(RuntimeError):
            with seeded.begin_nested():
                change(seeded, guard=outer)
                raise RuntimeError("rollback")
        assert count(seeded, RaceChange) == 0
        change(seeded, guard=outer)
    with pytest.raises(ChangeError):
        change(seeded, "expired", guard=outer)
    with seeded.begin_nested() as nested:
        with scope_guards(seeded, [ONE]) as inner:
            nested.rollback()
            with pytest.raises(ChangeError):
                change(seeded, "rolled-back", scopes=(ONE,), guard=inner)
    with scope_guards(seeded, [ONE]) as root:
        seeded.rollback()
        seeded.execute(select(1))
        with pytest.raises(ChangeError):
            change(seeded, "new-root", scopes=(ONE,), guard=root)


def test_rollback_remove_restores_notifications_and_scope_restrict(seeded):
    alice, _ = users(seeded)
    saved = put_saved_entry(seeded, alice, ONE)
    change(seeded, scopes=(ONE,))
    project_notifications(seeded, alice)
    with pytest.raises(RuntimeError):
        with seeded.begin_nested():
            delete_saved_entry(seeded, alice, saved.id)
            assert count(seeded, PersonalNotification) == 0
            raise RuntimeError("rollback")
    assert count(seeded, PersonalNotification) == 1
    with pytest.raises(IntegrityError):
        with seeded.begin_nested():
            seeded.execute(text("DELETE FROM entry_scope WHERE id=:scope"), {"scope": ONE})
    assert count(seeded, PersonalNotification) == 1


@pytest.mark.parametrize("save_first", [False, True])
def test_save_vs_uncommitted_record_has_linearized_baseline(seeded, database, save_first):
    alice, _ = users(seeded)
    account_id = alice.id
    seeded.commit()
    waiting = Event()
    with Session(database) as owner:
        if save_first:
            saved = put_saved_entry(owner, owner.get(Account, account_id), ONE)
            saved_id = saved.id
        else:
            change(owner, scopes=(ONE,))

        def competing():
            with Session(database) as other:
                other.execute(text("SET LOCAL lock_timeout='5s'"))

                def before(_conn, _cursor, statement, *_args):
                    if "pg_advisory_xact_lock" in statement:
                        waiting.set()

                event.listen(other.connection(), "before_cursor_execute", before)
                if save_first:
                    change(other, scopes=(ONE,))
                    result = None
                else:
                    entry = put_saved_entry(other, other.get(Account, account_id), ONE)
                    result = entry.id
                other.commit()
                return result

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(competing)
            try:
                assert waiting.wait(3) and not future.done()
            finally:
                owner.commit()
            result = future.result(timeout=8)
            if not save_first:
                saved_id = result
    with Session(database) as verify:
        entry = verify.get(SavedEntry, saved_id)
        assert entry.notifications_after_sequence == (0 if save_first else 1)
        assert project_notifications(verify, verify.get(Account, account_id)).inserted == (
            1 if save_first else 0
        )


@pytest.mark.parametrize("mode", ["conditional_savepoint", "create_savepoint", "rollback_only"])
def test_guard_tracks_effective_external_connection_transaction(seeded, database, mode):
    with database.connect() as connection:
        root = connection.begin()
        external = connection.begin_nested() if mode != "rollback_only" else root
        with Session(bind=connection, join_transaction_mode=mode) as session:
            with scope_guards(session, [ONE]) as guard:
                assert guard.database_root is root
                effective = connection.get_nested_transaction() or connection.get_transaction()
                effective.rollback()
                with pytest.raises(ChangeError):
                    change(session, scopes=(ONE,), guard=guard)
                assert root.is_active == (mode != "rollback_only")
            with pytest.warns(SAWarning, match="already deassociated"):
                session.rollback()
        if external.is_active:
            external.rollback()
        if root.is_active:
            root.rollback()


def test_multi_bind_is_rejected_before_guard(seeded, database):
    with Session(bind=database, binds={RaceChange: database.execution_options()}) as session:
        with pytest.raises(ChangeError, match="bind"):
            with scope_guards(session, [ONE]):
                pytest.fail("Unexpected guard")
        assert count(seeded, RaceChange) == 0


def test_projection_remove_readd_serializes_incarnation(seeded, database):
    alice, _ = users(seeded)
    account_id = alice.id
    old_id = put_saved_entry(seeded, alice, ONE).id
    change(seeded, scopes=(ONE,))
    seeded.commit()
    waiting = Event()
    with Session(database) as projector:
        assert project_notifications(projector, projector.get(Account, account_id)).inserted == 1

        def replace():
            with Session(database) as other:
                other.execute(text("SET LOCAL lock_timeout='5s'"))

                def before(_conn, _cursor, statement, *_args):
                    if "FOR UPDATE" in statement and "account" in statement:
                        waiting.set()

                event.listen(other.connection(), "before_cursor_execute", before)
                actor = other.get(Account, account_id)
                delete_saved_entry(other, actor, old_id)
                new = put_saved_entry(other, actor, ONE)
                value = (new.id, new.notifications_after_sequence)
                assert project_notifications(other, actor).inserted == 0
                other.commit()
                return value

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(replace)
            try:
                assert waiting.wait(3) and not future.done()
            finally:
                projector.commit()
            new_id, baseline = future.result(timeout=8)
            assert new_id != old_id and baseline == 1
    with Session(database) as verify:
        assert count(verify, PersonalNotification) == 0


@pytest.mark.parametrize("orm", [False, True])
def test_loaded_notifications_account_delete_database_cascade(seeded, orm):
    alice, bob = users(seeded)
    for user in (alice, bob):
        put_saved_entry(seeded, user, ONE)
    change(seeded, scopes=(ONE,))
    for user in (alice, bob):
        project_notifications(seeded, user)
    loaded = list(seeded.scalars(select(PersonalNotification)))
    assert len(loaded) == 2
    if orm:
        seeded.delete(alice)
        seeded.flush()
    else:
        delete_account(seeded, alice)
    assert list(seeded.scalars(select(PersonalNotification.account_id))) == [bob.id]


def test_migration_backfills_existing_saves_without_durable_default(seeded, database):
    alice, _ = users(seeded)
    saved_id = put_saved_entry(seeded, alice, ONE).id
    actor_id = alice.id
    seeded.commit()
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.downgrade(config, "a74d915e3c02")
    try:
        with database.begin() as connection:
            assert (
                connection.scalar(
                    text("SELECT count(*) FROM saved_entry WHERE id=:id"), {"id": saved_id}
                )
                == 1
            )
        command.upgrade(config, "head")
        command.check(config)
        assert seeded.get(SavedEntry, saved_id).notifications_after_sequence == 0
        assert (
            seeded.scalar(
                text(
                    "SELECT column_default FROM information_schema.columns "
                    "WHERE table_schema=current_schema() AND table_name='saved_entry' "
                    "AND column_name='notifications_after_sequence'"
                )
            )
            is None
        )
        with pytest.raises(IntegrityError) as failed:
            with seeded.begin_nested():
                seeded.execute(
                    text(
                        "INSERT INTO saved_entry (id,account_id,scope_id,status) "
                        "VALUES ('missing-baseline',:actor,:scope,'interested')"
                    ),
                    {"actor": actor_id, "scope": TWO},
                )
        assert failed.value.orig.sqlstate == "23502"
    finally:
        seeded.rollback()
        command.upgrade(config, "head")


def test_projection_large_batch_is_bounded_sql_and_reports_remaining(seeded):
    alice, _ = users(seeded)
    put_saved_entry(seeded, alice, ONE)
    seeded.execute(
        insert(RaceChange),
        [
            {
                "id": f"change-{i}",
                "race_id": "race-road-split",
                "event_key": f"fixture-{i}",
                "kind": "business",
                "signature": "a" * 64,
                "provenance": PROVENANCE,
            }
            for i in range(210)
        ],
    )
    seeded.execute(
        insert(ScopeChange),
        [
            {
                "change_id": f"change-{i}",
                "scope_id": ONE,
                "sequence": i + 1,
                "payload": {"before": {"name": "Before"}, "after": {"name": "After"}},
            }
            for i in range(210)
        ],
    )
    statements = []
    connection = seeded.connection()

    def observed(_conn, _cursor, statement, *_args):
        statements.append(statement)

    event.listen(connection, "before_cursor_execute", observed)
    try:
        first = project_notifications(seeded, alice, batch_size=128)
        assert (first.inserted, first.pending) == (128, True)
        assert len(statements) == 3
        statements.clear()
        second = project_notifications(seeded, alice, batch_size=128)
        assert (second.inserted, second.pending) == (82, False)
        assert len(statements) == 3
    finally:
        event.remove(connection, "before_cursor_execute", observed)
    assert count(seeded, PersonalNotification) == 210


@pytest.mark.parametrize("isolation", ["AUTOCOMMIT", "REPEATABLE READ"])
def test_guard_rejects_transaction_modes_that_break_subscription_baseline(
    seeded, database, isolation
):
    with Session(database.execution_options(isolation_level=isolation)) as session:
        with pytest.raises(ChangeError, match="READ COMMITTED"):
            with scope_guards(session, [ONE]):
                pytest.fail("Unexpected guard")


@pytest.mark.parametrize("batch", [True, 0, 1001])
def test_invalid_batch_is_pure_and_does_not_mutate(seeded, batch):
    alice, _ = users(seeded)
    with pytest.raises(ValueError):
        project_notifications(seeded, alice, batch_size=batch)
    assert count(seeded, PersonalNotification) == 0


def test_invalid_or_oversized_delta_and_sequence_overflow_leave_no_partial_event(seeded):
    with pytest.raises(ChangeError):
        change(seeded, after="x" * 16384)
    with pytest.raises(ChangeError):
        change(seeded, scopes=("scope-gravel",))
    assert count(seeded, RaceChange) == 0
    first = change(seeded, scopes=(ONE,))
    row = seeded.get(ScopeChange, (first, ONE))
    row.sequence = 9223372036854775807
    seeded.flush()
    with pytest.raises(ChangeError, match="exhausted"):
        change(seeded, "overflow", scopes=(ONE,))
    assert count(seeded, RaceChange) == 1
