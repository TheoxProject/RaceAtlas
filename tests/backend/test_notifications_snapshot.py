import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Event
from time import monotonic

import pytest
from sqlalchemy import func, insert, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from test_notifications import ONE, PROVENANCE, TWO, change, users
from test_notifications_api import KEY, read

from raceatlas.models import Account, PersonalNotification, RaceChange, ScopeChange
from raceatlas.notifications import project_notifications
from raceatlas.notifications_api import mark_all_notifications_read, read_notifications
from raceatlas.planning import delete_saved_entry, put_saved_entry
from raceatlas.planning_snapshot import PlanningLimitError, PlanningLimits


def test_virtual_count_over_thousand_includes_pending_batch_and_ack_all(seeded):
    alice, bob = users(seeded)
    put_saved_entry(seeded, alice, ONE)
    put_saved_entry(seeded, bob, TWO)
    now = datetime(2026, 11, 16, tzinfo=timezone.utc)
    seeded.execute(
        insert(RaceChange),
        [
            dict(
                id=f"synthetic-change-{i}",
                race_id="race-road-split",
                event_key=f"event-{i}",
                kind="business",
                signature=f"{i:064x}",
                provenance=PROVENANCE,
                created_at=now,
            )
            for i in range(1005)
        ],
    )
    seeded.execute(
        insert(ScopeChange),
        [
            dict(
                change_id=f"synthetic-change-{i}",
                scope_id=ONE,
                sequence=i + 1,
                payload={"before": {"name": "Before"}, "after": {"name": "After"}},
            )
            for i in range(1005)
        ],
    )
    seeded.commit()
    projected = project_notifications(seeded, alice)
    assert projected.inserted == 256 and projected.pending
    page = read(seeded, alice)
    assert page["unread_count"] == 1005 and len(page["items"]) == 50 and page["has_more"]
    all_keys = set()
    while True:
        keys = {(item["change_id"], item["scope_id"]) for item in page["items"]}
        assert not all_keys.intersection(keys)
        all_keys.update(keys)
        assert page["unread_count"] == 1005
        if not page["has_more"]:
            break
        page = read(seeded, alice, limit=100, cursor=page["next_cursor"])
    assert len(all_keys) == 1005
    mark_all_notifications_read(seeded, alice)
    seeded.commit()
    assert read(seeded, alice)["unread_count"] == 0 and read(seeded, bob)["unread_count"] == 0
    assert seeded.scalar(select(func.count()).select_from(PersonalNotification)) == 1005
    oldest_read = seeded.scalar(select(func.min(PersonalNotification.read_at)))
    mark_all_notifications_read(seeded, alice)
    seeded.commit()
    assert seeded.scalar(select(func.min(PersonalNotification.read_at))) == oldest_read


def wait_until_blocked(connection, pid, blocker_pid):
    deadline = monotonic() + 3
    pause = Event()
    while monotonic() < deadline:
        blockers = connection.scalar(select(func.pg_blocking_pids(pid)))
        if blocker_pid in blockers:
            return
        # Poll actual PG lock state; elapsed time is only a bound, never proof
        # that the INSERT SELECT has acquired its statement snapshot.
        pause.wait(0.01)
    raise AssertionError("ACK did not reach the row-lock snapshot barrier")


@pytest.mark.parametrize("source_before_snapshot", [False, True])
def test_ack_statement_snapshot_excludes_later_source_commit_even_with_older_timestamp(
    seeded, database, source_before_snapshot
):
    alice, _ = users(seeded)
    put_saved_entry(seeded, alice, ONE)
    actor_id = alice.id
    old = change(seeded, scopes=(ONE,))
    project_notifications(seeded, alice)
    seeded.commit()
    started = Event()
    worker_pid = []

    def acknowledge():
        with Session(database) as private:
            actor = private.get(Account, actor_id)
            worker_pid.append(private.scalar(select(func.pg_backend_pid())))
            started.set()
            mark_all_notifications_read(private, actor)
            private.commit()

    with Session(database) as source, Session(database) as blocker, database.connect() as monitor:
        new = change(source, "new-source", scopes=(ONE,))
        source.get(RaceChange, new).created_at = source.get(RaceChange, old).created_at - timedelta(
            days=1
        )
        source.flush()
        if source_before_snapshot:
            source.commit()
        # Existing unread PN is the barrier INSIDE ON CONFLICT after the real
        # INSERT SELECT snapshot, not a host before_cursor_execute approximation.
        blocker.scalar(
            select(PersonalNotification)
            .where(PersonalNotification.change_id == old)
            .with_for_update()
        )
        blocker_pid = blocker.scalar(select(func.pg_backend_pid()))
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(acknowledge)
            try:
                assert started.wait(3)
                wait_until_blocked(monitor, worker_pid[0], blocker_pid)
                if not source_before_snapshot:
                    source.commit()
            finally:
                blocker.rollback()
                source.rollback()
            future.result(timeout=5)
    seeded.expire_all()
    page = read(seeded, seeded.get(Account, actor_id))
    assert page["unread_count"] == (0 if source_before_snapshot else 1)
    later = next(item for item in page["items"] if item["change_id"] == new)
    assert (later["read_at"] is not None) == source_before_snapshot
    assert len(page["items"]) == 2


def test_ack_timeout_rolls_back_whole_statement_and_session_is_usable(seeded, database):
    alice, _ = users(seeded)
    put_saved_entry(seeded, alice, ONE)
    put_saved_entry(seeded, alice, TWO)
    actor_id = alice.id
    change(seeded)
    project_notifications(seeded, alice, batch_size=1)
    seeded.commit()
    with Session(database) as blocker, Session(database) as private:
        blocker.scalar(select(PersonalNotification).with_for_update())
        private.execute(text("SET LOCAL lock_timeout='50ms'"))
        with pytest.raises(OperationalError):
            mark_all_notifications_read(private, private.get(Account, actor_id))
        private.rollback()
        assert read(private, private.get(Account, actor_id))["unread_count"] == 2
        assert private.scalar(select(func.count()).select_from(PersonalNotification)) == 1
        assert private.scalar(select(PersonalNotification.read_at)) is None


def test_unsave_readd_and_account_delete_keep_other_scope_actor_and_no_old_candidates(seeded):
    alice, bob = users(seeded)
    a = put_saved_entry(seeded, alice, ONE)
    put_saved_entry(seeded, alice, TWO)
    put_saved_entry(seeded, bob, ONE)
    old_id = a.id
    change(seeded)
    mark_all_notifications_read(seeded, alice)
    seeded.commit()
    delete_saved_entry(seeded, alice, old_id)
    seeded.commit()
    replacement = put_saved_entry(seeded, alice, ONE)
    assert replacement.id != old_id and replacement.notifications_after_sequence == 1
    assert [item["scope_id"] for item in read(seeded, alice)["items"]] == [TWO]
    assert read(seeded, bob)["unread_count"] == 1
    change(seeded, "later")
    assert read(seeded, alice)["unread_count"] == 2
    seeded.delete(alice)
    seeded.commit()
    assert read(seeded, bob)["unread_count"] == 2
    assert seeded.scalar(select(func.count()).select_from(PersonalNotification)) == 0


@pytest.mark.parametrize(
    "limits", [PlanningLimits(response_bytes=128), PlanningLimits(text_bytes=4)]
)
def test_page_limits_refuse_explicitly_without_truncating_or_materializing(seeded, limits):
    alice, _ = users(seeded)
    put_saved_entry(seeded, alice, ONE)
    change(seeded, scopes=(ONE,))
    with pytest.raises(PlanningLimitError):
        read_notifications(seeded, alice, cursor_key=KEY, limits=limits)
    assert seeded.scalar(select(func.count()).select_from(PersonalNotification)) == 0
    assert json.loads(read_notifications(seeded, alice, cursor_key=KEY))["unread_count"] == 1
