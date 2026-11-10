import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import func, select, text

from raceatlas.ffc import (
    AdapterError,
    IdentityAttestation,
    WindowRequest,
    parse_calendar,
    parse_race,
)
from raceatlas.ffc.types import SourceKey
from raceatlas.models import (
    Competition,
    GeocodeCache,
    ImportItem,
    ImportRun,
    ImportWindow,
    Race,
    SourceAlias,
    SourceRevision,
)
from raceatlas.sync import AliasProof, CompetitionProof, LocationFact, WindowBatch, synchronize
from raceatlas.sync.geocoding import CenterCandidate, OfflineProvider
from raceatlas.sync.service import LOCK_KEY

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "fixtures/ffc/race.synthetic.html").read_text(encoding="utf-8")
NOW = datetime(2026, 11, 10, 16, tzinfo=timezone.utc)
WINDOW = WindowRequest(NOW.date(), NOW.date() + timedelta(days=6), "26")


def observation(number="SYNTHETIC001", *, html=HTML, checked=NOW, season=2027):
    return parse_race(
        html,
        source_url=f"https://competitions.ffc.fr/calendrier/competition/{season}/{number}/fictive/",
        checked_at=checked,
    )


def batch(*details, keys=None, checked=NOW, **kwargs):
    keys = tuple(item.key for item in details) if keys is None else keys
    links = "".join(
        f'<a href="/calendrier/competition/{key.season}/{key.race_number}/fictive/">Fictive</a>'
        for key in keys
    )
    html = (
        '<input name="debut" value="2026-11-10">'
        '<select name="nbjours"><option value="7" selected>7</option></select>'
        '<select name="departement"><option value="26" selected>26</option></select>'
        f'<div id="xInfoJourSelection">{len(keys)} épreuves</div>' + links
    )
    calendar = parse_calendar(
        html,
        source_url="https://competitions.ffc.fr/calendrier/",
        checked_at=checked,
        requested=WINDOW,
    )
    return WindowBatch(calendar, tuple(details), **kwargs)


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def identities(observed, stored):
    return IdentityAttestation(
        observed.key,
        stored.id,
        "explicit-test-review",
        tuple((new.token, old.id) for new, old in zip(observed.scopes, stored.scopes, strict=True)),
        tuple(
            (new.token, old.id)
            for new_scope, old_scope in zip(observed.scopes, stored.scopes, strict=True)
            for new, old in zip(new_scope.rules, old_scope.rules, strict=True)
        ),
    )


def test_fixture_sync_is_idempotent_audited_and_api_conformant(session, database, app):
    first = synchronize(database, [batch(observation())], checked_at=NOW)
    later = NOW + timedelta(hours=1)
    second = synchronize(
        database, [batch(observation(checked=later), checked=later)], checked_at=later
    )
    assert first.status == second.status == "success"
    assert (
        count(session, Race) == count(session, SourceRevision) == count(session, SourceAlias) == 1
    )
    assert (
        count(session, ImportRun) == count(session, ImportWindow) == count(session, ImportItem) == 2
    )
    race = session.scalar(select(Race))
    assert race.revision == 1
    response = app.test_client().get(f"/api/v1/races/{race.id}")
    assert response.status_code == 200
    schema = json.loads((ROOT / "contracts/catalog.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(
        {"$defs": schema["$defs"], "$ref": "#/$defs/Race"}, format_checker=FormatChecker()
    ).validate(response.json)
    assert response.json["source"]["source_season"] == 2027
    assert response.json["start_date"] == "2026-11-11"
    assert response.json["location"] is None
    assert "PRIVATE_SENTINEL" not in str(session.scalar(select(SourceRevision)).facts)


def test_title_date_and_grouping_changes_preserve_scope_ids(session, database):
    synchronize(database, [batch(observation())], checked_at=NOW)
    race = session.scalar(select(Race))
    original_id, scope_ids = race.id, [scope.id for scope in race.scopes]
    session.add(Competition(id="competition-reviewed", name="Fictive", grouping_evidence="proof"))
    session.commit()
    changed = observation(
        html=HTML.replace("collines", "vallons").replace("2026-11-11", "2026-11-12")
    )
    proof = CompetitionProof(changed.key, "competition-reviewed", 1, "grouping-proof")
    result = synchronize(database, [batch(changed, competitions=(proof,))], checked_at=NOW)
    session.expire_all()
    stored = session.get(Race, original_id)
    assert result.status == "success"
    assert stored.name.endswith("vallons")
    assert stored.start_date.isoformat() == "2026-11-12"
    assert stored.competition_id == "competition-reviewed"
    assert [scope.id for scope in stored.scopes] == scope_ids
    assert stored.revision == 2
    assert count(session, SourceRevision) == 2


def test_unverified_reordered_scopes_quarantined_without_graph_reassignment(session, database):
    synchronize(database, [batch(observation())], checked_at=NOW)
    stored = session.scalar(select(Race))
    scope_ids = [scope.id for scope in stored.scopes]
    changed = observation()
    changed = replace(changed, scopes=tuple(reversed(changed.scopes)))
    result = synchronize(database, [batch(changed)], checked_at=NOW)
    session.expire_all()
    assert result.status == "failed"
    assert [scope.id for scope in session.get(Race, stored.id).scopes] == scope_ids
    assert count(session, SourceRevision) == 1
    assert session.scalars(select(ImportItem).where(ImportItem.status == "review")).first()


def test_attested_scope_change_preserves_all_ids_and_records_evidence(session, database):
    synchronize(database, [batch(observation())], checked_at=NOW)
    stored = session.scalar(select(Race))
    old_ids = [scope.id for scope in stored.scopes]
    changed = observation(html=HTML.replace("Restriction fictive A", "Restriction fictive B"))
    proof = identities(changed, stored)
    result = synchronize(database, [batch(changed, identities=(proof,))], checked_at=NOW)
    session.expire_all()
    assert result.status == "success"
    assert [scope.id for scope in session.get(Race, stored.id).scopes] == old_ids
    assert session.get(Race, stored.id).revision == 2
    assert count(session, SourceRevision) == 2
    item = session.scalars(select(ImportItem).where(ImportItem.status == "updated")).one()
    assert item.observed["identity_evidence"] == "explicit-test-review"


def test_same_rule_facts_with_distinct_scope_labels_reorder_requires_review(session, database):
    first = observation()
    a = first.scopes[0]
    b = replace(a, token="other-observation-token", raw_label="Distinct second published list")
    first = replace(first, scopes=(a, b))
    synchronize(database, [batch(first)], checked_at=NOW)
    second = replace(first, scopes=(b, a))
    assert synchronize(database, [batch(second)], checked_at=NOW).status == "failed"
    assert count(session, SourceRevision) == 1


def test_alias_requires_proof_keeps_original_reference_and_replays_idempotently(session, database):
    original = observation()
    synchronize(database, [batch(original)], checked_at=NOW)
    stored = session.scalar(select(Race))
    changed = observation("CORRECTED", season=2028)
    proof = AliasProof(changed.key, stored.id, original.key, 1, "source-correction-proof", NOW)
    for _ in range(2):
        assert (
            synchronize(database, [batch(changed, aliases=(proof,))], checked_at=NOW).status
            == "success"
        )
    session.expire_all()
    assert count(session, Race) == count(session, SourceRevision) == 1
    assert count(session, SourceAlias) == 2
    assert session.get(Race, stored.id).source.source_season == 2028
    assert synchronize(database, [batch(original)], checked_at=NOW).status == "success"
    assert count(session, Race) == 1


@pytest.mark.parametrize("kind", ["empty", "stale", "conflict", "future"])
def test_invalid_alias_proofs_never_reassign_existing_identity(session, database, kind):
    original, other = observation(), observation("OTHER")
    synchronize(database, [batch(original, other)], checked_at=NOW)
    stored = session.scalar(select(Race).where(Race.source.has(race_number="SYNTHETIC001")))
    changed = observation("OTHER" if kind == "conflict" else "CORRECTED")
    proof = AliasProof(changed.key, stored.id, original.key, 1, "alias-proof", NOW)
    if kind == "empty":
        proof = replace(proof, evidence_id=" ")
    if kind == "stale":
        proof = replace(proof, expected_revision=99)
    if kind == "future":
        proof = replace(proof, decided_at=NOW + timedelta(days=1))
    assert (
        synchronize(database, [batch(changed, aliases=(proof,))], checked_at=NOW).status == "failed"
    )
    assert count(session, Race) == 2
    assert count(session, SourceAlias) == 2


def test_only_complete_run_marks_absence_to_verify_preserving_cancelled(session, database):
    first = observation()
    cancelled = observation("OTHER", html=HTML.replace("Programmée", "Annulée"))
    synchronize(database, [batch(first, cancelled)], checked_at=NOW)
    result = synchronize(database, [batch(first)], checked_at=NOW)
    session.expire_all()
    missing = session.scalar(select(Race).where(Race.status == "cancelled"))
    assert result.status == "success" and result.missing_marked == 1
    assert missing.source_presence == "to_verify" and missing.status == "cancelled"
    assert count(session, SourceRevision) == 2


def test_partial_independent_window_imports_positives_but_defers_all_absence(session, database):
    first, old, new = observation(), observation("OLD"), observation("NEW")
    synchronize(database, [batch(first, old)], checked_at=NOW)
    failed = batch(keys=(SourceKey(2027, "BROKEN"),))
    result = synchronize(database, [batch(first, new), failed], checked_at=NOW)
    session.expire_all()
    assert result.status == "partial" and result.missing_marked == 0
    assert count(session, Race) == 3
    assert (
        session.scalar(select(Race).where(Race.source.has(race_number="OLD"))).source_presence
        == "present"
    )
    retry = synchronize(database, [batch(first, old, new)], checked_at=NOW)
    assert retry.status == "success"
    assert count(session, Race) == count(session, SourceRevision) == 3


def test_global_presence_prevents_overlap_false_absence(session, database):
    first, other = observation(), observation("OTHER")
    synchronize(database, [batch(first, other)], checked_at=NOW)
    result = synchronize(database, [batch(first), batch(other)], checked_at=NOW)
    session.expire_all()
    assert result.status == "success" and result.missing_marked == 0
    assert all(race.source_presence == "present" for race in session.scalars(select(Race)))


def test_incoherent_window_and_conflicting_details_cannot_change_catalog(session, database):
    original = observation()
    synchronize(database, [batch(original)], checked_at=NOW)
    changed = observation(html=HTML.replace("collines", "vallons"))
    bad = batch(changed)
    bad = replace(bad, calendar=replace(bad.calendar, effective_department="38"))
    assert synchronize(database, [bad], checked_at=NOW).status == "failed"
    assert (
        synchronize(database, [batch(original), batch(changed)], checked_at=NOW).status == "failed"
    )
    session.expire_all()
    assert session.scalar(select(Race)).name.endswith("collines")
    assert count(session, SourceRevision) == 1


def test_stale_and_partial_details_preserve_known_data(session, database):
    original = observation()
    synchronize(database, [batch(original)], checked_at=NOW)
    partial = observation(html=HTML.replace("<dt>Organisateur</dt><dd>Club fictif</dd>", ""))
    assert synchronize(database, [batch(partial)], checked_at=NOW).status == "failed"
    stale = replace(original, checked_at=NOW - timedelta(days=1))
    assert synchronize(database, [batch(stale)], checked_at=NOW).status == "failed"
    assert session.scalar(select(Race)).organizer == "Club fictif"


def test_item_savepoint_rolls_back_storage_failure_and_retry_has_no_duplicate(session, database):
    broken = replace(observation(), name=None)
    good = observation("OTHER")
    result = synchronize(database, [batch(broken, good)], checked_at=NOW)
    assert result.status == "partial"
    assert count(session, Race) == count(session, SourceRevision) == 1
    assert session.scalar(select(ImportItem).where(ImportItem.diagnostic == "storage_error"))
    assert synchronize(database, [batch(observation(), good)], checked_at=NOW).status == "success"
    assert count(session, Race) == count(session, SourceRevision) == 2


def test_advisory_lock_prevents_competing_import_writers(database):
    with database.connect() as connection:
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": LOCK_KEY})
        connection.commit()
        try:
            with pytest.raises(AdapterError, match="import_busy"):
                synchronize(database, [batch(observation())], checked_at=NOW)
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
            connection.commit()


def test_explicit_center_binding_cached_and_known_center_survives_provider_error(session, database):
    observed = observation()
    fact = LocationFact(observed.key, "Commune fictive", "26", "source-location-proof", "26999")
    calls = []

    def lookup(_):
        calls.append(1)
        return [CenterCandidate("26999", "Commune fictive", "26", 4.9, 45.1)]

    provider = OfflineProvider("offline-test", "v1", lookup)
    for _ in range(2):
        assert (
            synchronize(
                database, [batch(observed, locations=(fact,))], checked_at=NOW, provider=provider
            ).status
            == "success"
        )
    assert len(calls) == 1
    race = session.scalar(select(Race))
    commune_id = race.commune_id

    def failure(_):
        raise RuntimeError("PRIVATE_PROVIDER_SECRET")

    failed_provider = OfflineProvider("offline-test", "v2", failure)
    result = synchronize(
        database, [batch(observed, locations=(fact,))], checked_at=NOW, provider=failed_provider
    )
    session.expire_all()
    assert result.status == "partial"
    assert session.get(Race, race.id).commune_id == commune_id
    assert count(session, GeocodeCache) == 2
    assert "PRIVATE_PROVIDER_SECRET" not in str(
        session.scalars(select(GeocodeCache.diagnostic)).all()
    )
    assert count(session, SourceRevision) == 1
