from dataclasses import replace
from datetime import timedelta, timezone

import pytest
import test_sync as source
from sqlalchemy import func, select

from raceatlas.changes import ChangeError
from raceatlas.models import (
    Account,
    ImportItem,
    ImportWindow,
    PersonalNotification,
    Race,
    RaceChange,
    ScopeChange,
    SourceRevision,
)
from raceatlas.notifications import project_notifications
from raceatlas.planning import create_account, put_saved_entry
from raceatlas.sync import service, synchronize


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def initial(session, database):
    observed = source.observation()
    result = synchronize(database, [source.batch(observed)], checked_at=source.NOW)
    assert result.status == "success"
    race = session.scalar(select(Race))
    return observed, race.id, tuple(scope.id for scope in race.scopes)


def subscribe(session, scopes, status="interested"):
    alice = create_account(session, "alice@example.test")
    bob = create_account(session, "bob@example.test")
    for scope in scopes:
        put_saved_entry(session, alice, scope, status)
    put_saved_entry(session, bob, scopes[-1], "completed")
    ids = alice.id, bob.id
    session.commit()
    return ids


@pytest.mark.parametrize("status", ["interested", "planned", "registered", "completed"])
def test_actual_import_business_change_projects_exact_scopes_once(session, database, status):
    observed, race_id, scopes = initial(session, database)
    alice, bob = subscribe(session, scopes, status)
    later = source.NOW + timedelta(hours=1)
    changed = replace(
        observed,
        name="Synthetic report",
        start_date=observed.start_date + timedelta(days=1),
        end_date=observed.end_date + timedelta(days=1),
        checked_at=later,
    )
    assert (
        synchronize(database, [source.batch(changed, checked=later)], checked_at=later).status
        == "success"
    )
    session.expire_all()
    revision = session.scalar(
        select(SourceRevision).where(
            SourceRevision.race_id == race_id, SourceRevision.revision == 2
        )
    )
    recorded = session.scalar(select(RaceChange))
    assert recorded.event_key == "revision:" + revision.id
    assert (
        recorded.provenance["checked_at"]
        == revision.checked_at.astimezone(timezone.utc).isoformat()
    )
    assert set(session.scalars(select(ScopeChange.scope_id))) == set(scopes)
    assert project_notifications(session, session.get(Account, alice)).inserted == len(scopes)
    assert project_notifications(session, session.get(Account, bob)).inserted == 1
    assert project_notifications(session, session.get(Account, alice)).inserted == 0
    session.commit()
    assert (
        synchronize(database, [source.batch(changed, checked=later)], checked_at=later).status
        == "success"
    )
    newest = later + timedelta(hours=1)
    assert (
        synchronize(
            database,
            [source.batch(replace(changed, checked_at=newest), checked=newest)],
            checked_at=newest,
        ).status
        == "success"
    )
    assert count(session, RaceChange) == 1


def test_rule_change_only_targets_its_own_scope_and_reorder_is_not_change(session, database):
    observed, race_id, scopes = initial(session, database)
    alice, bob = subscribe(session, scopes)
    later = source.NOW + timedelta(hours=1)
    first = observed.scopes[0]
    rule = first.rules[0]
    updated_rule = replace(
        rule, restrictions=replace(rule.restrictions, other_text="Synthetic new restriction")
    )
    changed = replace(
        observed,
        checked_at=later,
        scopes=(replace(first, rules=(updated_rule, *first.rules[1:])), *observed.scopes[1:]),
    )
    stored = session.get(Race, race_id)
    proof = source.identities(changed, stored)
    session.commit()
    assert (
        synchronize(
            database, [source.batch(changed, checked=later, identities=(proof,))], checked_at=later
        ).status
        == "success"
    )
    assert list(session.scalars(select(ScopeChange.scope_id))) == [scopes[0]]
    assert project_notifications(session, session.get(Account, alice)).inserted == 1
    assert project_notifications(session, session.get(Account, bob)).inserted == 0
    session.commit()
    reordered = replace(
        changed, checked_at=later + timedelta(hours=1), scopes=tuple(reversed(changed.scopes))
    )
    stored = session.get(Race, race_id)
    original = {scope.id: scope for scope in stored.scopes}
    # Binding follows identities, not the new displayed rank.
    proof = replace(
        source.identities(changed, stored),
        key=reordered.key,
        scope_ids=tuple(
            (item.token, scopes[len(scopes) - i - 1]) for i, item in enumerate(reordered.scopes)
        ),
        rule_ids=tuple(
            (
                rule.token,
                next(
                    old.id
                    for old in original[scopes[len(scopes) - i - 1]].rules
                    if old.raw_label == rule.raw_label
                ),
            )
            for i, scope in enumerate(reordered.scopes)
            for rule in scope.rules
        ),
    )
    session.commit()
    assert (
        synchronize(
            database,
            [source.batch(reordered, checked=reordered.checked_at, identities=(proof,))],
            checked_at=reordered.checked_at,
        ).status
        == "success"
    )
    assert count(session, RaceChange) == 1


def test_successive_runs_keep_a_b_a_b_mutation_incarnations(session, database):
    observed, _, scopes = initial(session, database)
    subscribe(session, scopes)
    for index, name in enumerate(("Synthetic B", observed.name, "Synthetic B"), start=1):
        now = source.NOW + timedelta(hours=index)
        value = replace(observed, name=name, checked_at=now)
        assert (
            synchronize(database, [source.batch(value, checked=now)], checked_at=now).status
            == "success"
        )
    assert count(session, RaceChange) == 3
    assert len(set(session.scalars(select(RaceChange.event_key)))) == 3


def test_created_window_one_then_identical_window_two_has_fresh_inventory(
    session, database, monkeypatch
):
    observed = source.observation()
    seen = []
    original = service._window_scope_ids

    def inventory(*args):
        result = original(*args)
        seen.append(len(result))
        return result

    monkeypatch.setattr(service, "_window_scope_ids", inventory)
    later = source.NOW + timedelta(hours=1)
    result = synchronize(
        database,
        [source.batch(observed), source.batch(replace(observed, checked_at=later), checked=later)],
        checked_at=later,
    )
    assert result.status == "success" and seen[0] == 0 and seen[1] > 0
    assert count(session, Race) == 1 and count(session, SourceRevision) == 1
    assert count(session, RaceChange) == 0


def test_restoring_presence_records_even_when_business_unchanged(session, database):
    observed, race_id, scopes = initial(session, database)
    alice, _ = subscribe(session, scopes)
    missing = source.NOW + timedelta(hours=1)
    synchronize(database, [source.batch(keys=(), checked=missing)], checked_at=missing)
    session.expire_all()
    assert session.get(Race, race_id).source_presence == "to_verify"
    assert count(session, RaceChange) == 1  # Final absence is now recorded by N1B-2.
    now = missing + timedelta(hours=1)
    restored = replace(observed, checked_at=now)
    assert (
        synchronize(database, [source.batch(restored, checked=now)], checked_at=now).status
        == "success"
    )
    session.expire_all()
    assert session.get(Race, race_id).source_presence == "present"
    assert count(session, SourceRevision) == 1
    assert count(session, RaceChange) == 2
    assert set(session.scalars(select(RaceChange.kind))) == {"presence"}
    for before, after, checked, evidence_prefix in (
        ("present", "to_verify", missing, "window:"),
        ("to_verify", "present", now, "run:"),
    ):
        change = next(
            row
            for row in session.scalars(select(RaceChange))
            if row.provenance["checked_at"] == checked.isoformat()
        )
        targets = list(
            session.scalars(select(ScopeChange).where(ScopeChange.change_id == change.id))
        )
        assert {row.scope_id for row in targets} == set(scopes)
        assert all(
            row.payload
            == {"before": {"source_presence": before}, "after": {"source_presence": after}}
            for row in targets
        )
        assert change.provenance["evidence_id"].startswith(evidence_prefix)
        assert change.provenance["source_url"] == (
            source.batch().calendar.source_url if before == "present" else observed.source_url
        )
        assert change.provenance["normalization_version"] == observed.normalization_version
    assert project_notifications(session, session.get(Account, alice)).inserted == 2 * len(scopes)


def test_record_failure_rolls_back_source_revision_and_event_together(
    session, database, monkeypatch
):
    observed, race_id, scopes = initial(session, database)
    subscribe(session, scopes)
    original = service.record_change

    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise ChangeError("Synthetic post-record failure")

    monkeypatch.setattr(service, "record_change", fail_after_write)
    later = source.NOW + timedelta(hours=1)
    changed = replace(observed, name="Should roll back", checked_at=later)
    result = synchronize(database, [source.batch(changed, checked=later)], checked_at=later)
    session.expire_all()
    assert result.status == "failed"
    assert session.get(Race, race_id).name == observed.name
    assert count(session, SourceRevision) == 1
    assert (
        count(session, RaceChange)
        == count(session, ScopeChange)
        == count(session, PersonalNotification)
        == 0
    )
    assert (
        session.scalar(
            select(ImportItem.diagnostic)
            .join(ImportWindow)
            .where(ImportWindow.run_id == result.run_id)
        )
        == "change_record_error"
    )
