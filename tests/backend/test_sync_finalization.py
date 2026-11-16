from dataclasses import FrozenInstanceError, replace
from datetime import timedelta, timezone

import pytest
import test_sync as source
from sqlalchemy import event, select
from test_sync_notifications import count, initial, subscribe

from raceatlas.catalog.coverage import coverage_document
from raceatlas.models import (
    Account,
    CatalogState,
    ImportItem,
    ImportRun,
    ImportWindow,
    Race,
    RaceChange,
    ScopeChange,
    SourceRevision,
)
from raceatlas.notifications import project_notifications
from raceatlas.sync import service, synchronize
from raceatlas.sync.final_plan import plan_finalization


def coverage(session):
    return coverage_document(session, session.get(CatalogState, 1))


@pytest.mark.parametrize("status", ["interested", "planned", "registered", "completed"])
def test_absence_import_projects_once_then_metadata_and_restore_preserve_counters(
    session, database, status
):
    observed, race_id, scopes = initial(session, database)
    alice, bob = subscribe(session, scopes, status)
    absent = source.NOW + timedelta(hours=1)
    result = synchronize(database, [source.batch(keys=(), checked=absent)], checked_at=absent)
    session.expire_all()
    race = session.get(Race, race_id)
    assert result.status == "success" and result.missing_marked == 1
    assert race.source_presence == "to_verify" and race.status == observed.status
    assert race.revision == 1 and count(session, SourceRevision) == 1
    assert project_notifications(session, session.get(Account, alice)).inserted == len(scopes)
    assert project_notifications(session, session.get(Account, bob)).inserted == 1
    session.commit()
    newer = absent + timedelta(minutes=30)
    repeated = synchronize(database, [source.batch(keys=(), checked=newer)], checked_at=newer)
    session.expire_all()
    assert repeated.status == "success" and repeated.missing_marked == 0
    assert count(session, RaceChange) == 1
    assert session.get(Race, race_id).source.presence_checked_at.astimezone(timezone.utc) == newer
    assert project_notifications(session, session.get(Account, alice)).inserted == 0
    session.commit()
    restored = newer + timedelta(minutes=30)
    assert (
        synchronize(
            database,
            [source.batch(replace(observed, checked_at=restored), checked=restored)],
            checked_at=restored,
        ).status
        == "success"
    )
    session.expire_all()
    assert session.get(Race, race_id).source_presence == "present"
    assert count(session, RaceChange) == 2 and count(session, SourceRevision) == 1
    assert project_notifications(session, session.get(Account, alice)).inserted == len(scopes)


def test_absence_provenance_is_actual_latest_calendar_not_race_page_or_now(session, database):
    cancelled = source.observation(html=source.HTML.replace("Programmée", "Annulée"))
    synchronize(database, [source.batch(cancelled)], checked_at=source.NOW)
    race = session.scalar(select(Race))
    race_id, source_url = race.id, race.source.source_url
    revision_id = session.scalar(select(SourceRevision.id))
    session.commit()
    older_at, newer_at = source.NOW + timedelta(minutes=10), source.NOW + timedelta(hours=1)
    old, new = source.batch(keys=(), checked=older_at), source.batch(keys=(), checked=newer_at)
    old = replace(
        old, calendar=replace(old.calendar, source_url="https://example.test/calendar/older")
    )
    new = replace(
        new, calendar=replace(new.calendar, source_url="https://example.test/calendar/newer")
    )
    run_now = newer_at + timedelta(hours=1)
    result = synchronize(database, [new, old], checked_at=run_now)
    session.expire_all()
    row = session.scalar(select(RaceChange))
    witness = session.scalar(
        select(ImportWindow).where(
            ImportWindow.run_id == result.run_id, ImportWindow.source_url == new.calendar.source_url
        )
    )
    assert row.kind == "presence" and row.provenance == {
        "source_url": new.calendar.source_url,
        "checked_at": newer_at.isoformat(),
        "normalization_version": session.get(ImportRun, result.run_id).parser_version,
        "evidence_id": "window:" + witness.id,
    }
    assert row.provenance["source_url"] != source_url
    assert session.get(Race, race_id).status == "cancelled"
    assert session.get(Race, race_id).source.checked_at.astimezone(timezone.utc) == source.NOW
    assert session.scalar(select(SourceRevision.id)) == revision_id
    assert all(
        scope.payload
        == {"before": {"source_presence": "present"}, "after": {"source_presence": "to_verify"}}
        for scope in session.scalars(select(ScopeChange))
    )


@pytest.mark.parametrize("kind", ["stale", "partial"])
def test_non_admissible_windows_do_not_infer_missing_and_coverage_is_incomplete(
    session, database, kind
):
    _, race_id, _ = initial(session, database)
    later = source.NOW + timedelta(hours=2)
    if kind == "stale":
        batches = [source.batch(keys=(), checked=source.NOW - timedelta(hours=1))]
    else:
        good = source.observation("INDEPENDENT", checked=later)
        missing = source.observation("MISSING", checked=later)
        batches = [
            source.batch(good, checked=later),
            source.batch(keys=(missing.key,), checked=later),
        ]
    result = synchronize(database, batches, checked_at=later)
    session.expire_all()
    assert result.status in {"failed", "partial"} and result.missing_marked == 0
    assert session.get(Race, race_id).source_presence == "present"
    assert count(session, RaceChange) == 0
    assert coverage(session)["status"] == "incomplete"


def test_final_planner_is_pure_frozen_and_preserves_historical_promotions(session, database):
    _, race_id, _ = initial(session, database)
    item = session.scalar(select(ImportItem))
    window = session.get(ImportWindow, item.window_id)
    item.status, item.diagnostic = "error", "stale_observation"
    window.status, window.diagnostics = "partial", ["stale_observation"]
    run_id = window.run_id
    session.commit()
    inputs = service._load_final_inputs(session, run_id, source.NOW, {race_id})
    statements = []

    def observed(_conn, _cursor, statement, *_args):
        statements.append(statement)

    event.listen(database, "before_cursor_execute", observed)
    try:
        plan = plan_finalization(inputs)
        assert statements == [] and not session.dirty and not session.new and not session.deleted
    finally:
        event.remove(database, "before_cursor_execute", observed)
    assert plan.run_status == "success" and not plan.transitions and not plan.scope_ids
    assert plan.items[0].diagnostic == "historical_duplicate"
    assert plan.windows[0].status == "success" and plan.windows[0].diagnostics == ()
    assert inputs.windows[0].status == session.get(ImportWindow, window.id).status == "partial"
    with pytest.raises(FrozenInstanceError):
        plan.run_status = "failed"
