import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

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
    audit = session.scalars(select(ImportItem).order_by(ImportItem.id)).first()
    assert audit.observed["location_fact"]["evidence_id"] == "source-location-proof"
    assert audit.observed["geocoding_provider"] == {"name": "offline-test", "version": "v1"}
    race = session.scalar(select(Race))
    commune_id = race.commune_id

    def failure(_):
        raise RuntimeError("PRIVATE_PROVIDER_SECRET")

    failed_provider = OfflineProvider("offline-test", "v2", failure)
    result = synchronize(
        database, [batch(observed, locations=(fact,))], checked_at=NOW, provider=failed_provider
    )
    session.expire_all()
    assert result.status == "failed"
    assert session.get(Race, race.id).commune_id == commune_id
    assert count(session, GeocodeCache) == 2
    assert "PRIVATE_PROVIDER_SECRET" not in str(
        session.scalars(select(GeocodeCache.diagnostic)).all()
    )
    assert count(session, SourceRevision) == 1


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE import_run SET status='invented'",
        "UPDATE import_run SET finished_at=started_at - interval '1 second'",
        "UPDATE import_window SET displayed_count=-1",
        "UPDATE import_item SET status='invented'",
        "UPDATE source_alias SET evidence_id=' '",
        "UPDATE source_alias SET source_season=1999",
        "UPDATE source_alias SET provider='synthetic'",
        "UPDATE source_revision SET revision=0",
        "UPDATE source_revision SET business_hash='invalid'",
        "INSERT INTO source_alias SELECT id || '-duplicate',provider,source_season,race_number,"
        "race_id,evidence_id,decided_at FROM source_alias LIMIT 1",
        "INSERT INTO source_revision SELECT id || '-duplicate',race_id,run_id,revision,"
        "business_hash,facts,normalization_version,source_url,checked_at "
        "FROM source_revision LIMIT 1",
    ],
)
def test_postgresql_enforces_new_audit_and_identity_constraints(session, database, statement):
    from sqlalchemy.exc import IntegrityError

    synchronize(database, [batch(observation())], checked_at=NOW)
    with pytest.raises(IntegrityError):
        session.execute(text(statement))
        session.commit()
    session.rollback()


def test_negative_geocoder_result_imports_unlocated_and_preserves_known_center_without_fact(
    session, database, app
):
    observed = observation()
    fact = LocationFact(observed.key, "Commune fictive", "26", "source-proof", "26999")
    negative = OfflineProvider("offline", "negative", lambda _: ())
    result = synchronize(
        database, [batch(observed, locations=(fact,))], checked_at=NOW, provider=negative
    )
    assert result.status == "success"
    stored = session.scalar(select(Race))
    assert app.test_client().get(f"/api/v1/races/{stored.id}").json["location"] is None
    positive = OfflineProvider(
        "offline",
        "positive",
        lambda _: (CenterCandidate("26999", "Commune fictive", "26", 4.9, 45.1),),
    )
    result = synchronize(
        database, [batch(observed, locations=(fact,))], checked_at=NOW, provider=positive
    )
    assert result.status == "success"
    response = app.test_client().get(f"/api/v1/races/{stored.id}").json
    assert response["location"]["coordinates"] == [4.9, 45.1]
    assert response["location"]["precision"] == "commune_center"
    assert response["location"]["provenance"] == "synthetic"
    assert response["location"]["insee_code"] == "26999"
    assert synchronize(database, [batch(observed)], checked_at=NOW).status == "success"
    assert (
        app.test_client().get(f"/api/v1/races/{stored.id}").json["location"] == response["location"]
    )


def test_department_change_with_known_center_is_quarantined(session, database):
    observed = observation()
    fact = LocationFact(observed.key, "Commune fictive", "26", "source-proof", "26999")
    provider = OfflineProvider(
        "offline", "v1", lambda _: (CenterCandidate("26999", "Commune fictive", "26", 4.9, 45.1),)
    )
    synchronize(database, [batch(observed, locations=(fact,))], checked_at=NOW, provider=provider)
    stored = session.scalar(select(Race))
    previous_center = stored.commune_id
    changed = observation(html=HTML.replace("<dd>26</dd>", "<dd>38</dd>"))
    changed_batch = batch(changed)
    cal = replace(
        changed_batch.calendar,
        requested=replace(WINDOW, department="38"),
        effective_department="38",
    )
    assert (
        synchronize(database, [replace(changed_batch, calendar=cal)], checked_at=NOW).status
        == "failed"
    )
    session.expire_all()
    assert session.get(Race, stored.id).department == "26"
    assert session.get(Race, stored.id).commune_id == previous_center


def test_geocoder_failure_defers_absence_for_entire_run(session, database):
    first, other = observation(), observation("OTHER")
    synchronize(database, [batch(first, other)], checked_at=NOW)
    fact = LocationFact(first.key, "Commune fictive", "26", "source-proof", "26999")
    provider = OfflineProvider(
        "offline", "v1", lambda _: (CenterCandidate("38999", "Wrong department", "38", 4.9, 45.1),)
    )
    result = synchronize(
        database, [batch(first, locations=(fact,))], checked_at=NOW, provider=provider
    )
    session.expire_all()
    assert result.status == "failed" and result.missing_marked == 0
    assert all(race.source_presence == "present" for race in session.scalars(select(Race)))


def test_inconsistent_location_binding_in_overlapping_windows_cannot_change_catalog(
    session, database
):
    observed = observation()
    fact = LocationFact(observed.key, "Commune fictive", "26", "source-proof", "26999")
    result = synchronize(
        database, [batch(observed), batch(observed, locations=(fact,))], checked_at=NOW
    )
    assert result.status == "failed"
    assert count(session, Race) == 0


def test_invalid_detail_parse_diagnostic_is_audited_without_raw_source(session, database):
    from raceatlas.sync import DetailFailure

    original = observation()
    invalid = HTML.replace("<dd>Route</dd>", "<dd>Unknown</dd>")
    with pytest.raises(AdapterError) as error:
        observation(html=invalid)
    failed = batch(
        keys=(original.key,), failures=(DetailFailure(original.key, error.value.diagnostic.code),)
    )
    result = synchronize(database, [failed], checked_at=NOW)
    assert result.status == "failed"
    item = session.scalar(select(ImportItem))
    assert item.diagnostic == "unknown_discipline" and item.observed is None
    assert count(session, Race) == 0


def test_unknown_scope_revision_keeps_known_graph_and_audits_needs_review(session, database):
    original = observation()
    synchronize(database, [batch(original)], checked_at=NOW)
    changed = observation(html=HTML.replace("Liste fictive A", "Reorganized list"))
    assert synchronize(database, [batch(changed)], checked_at=NOW).status == "failed"
    item = session.scalar(select(ImportItem).where(ImportItem.status == "review"))
    assert item.observed["identity_status"] == "needs_review"
    assert session.scalar(select(Race)).scopes[0].raw_label.startswith("Liste fictive A")


def test_replayed_grouping_proof_is_idempotent_after_revision_increment(session, database):
    observed = observation()
    session.add(Competition(id="group-replay", name="Fictive", grouping_evidence="proof"))
    session.commit()
    proof = CompetitionProof(observed.key, "group-replay", 0, "initial-group-proof")
    for _ in range(2):
        result = synchronize(database, [batch(observed, competitions=(proof,))], checked_at=NOW)
        assert result.status == "success"
    assert count(session, SourceRevision) == count(session, Race) == 1


def test_old_empty_window_cannot_mark_newer_observation_missing(session, database):
    later = NOW + timedelta(hours=1)
    synchronize(database, [batch(observation(checked=later), checked=later)], checked_at=later)
    result = synchronize(database, [batch()], checked_at=later + timedelta(hours=1))
    assert result.status == "failed" and result.missing_marked == 0
    assert session.scalar(select(Race)).source_presence == "present"
    assert session.scalar(
        select(ImportWindow).where(ImportWindow.run_id == result.run_id)
    ).diagnostics == ["stale_window"]


@pytest.mark.parametrize("code", ["", None, "PRIVATE RAW MESSAGE"])
def test_invalid_failure_codes_cannot_allow_missing_inference(session, database, code):
    from raceatlas.sync import DetailFailure

    observed = observation()
    synchronize(database, [batch(observed)], checked_at=NOW)
    failed = batch(keys=(observed.key,), failures=(DetailFailure(observed.key, code),))
    result = synchronize(database, [failed], checked_at=NOW)
    assert result.status == "failed" and result.missing_marked == 0
    assert session.scalar(select(Race)).source_presence == "present"


def test_no_windows_is_audited_as_failed_without_missing_inference(session, database):
    synchronize(database, [batch(observation())], checked_at=NOW)
    result = synchronize(database, [], checked_at=NOW)
    assert result.status == "failed" and result.missing_marked == 0
    assert session.scalar(select(Race)).source_presence == "present"
    assert session.get(ImportRun, result.run_id).status == "failed"


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("introduce_alias", [False, True])
@pytest.mark.parametrize("later_minutes", [0, 1])
def test_contradictory_aliases_quarantine_same_race_independently_of_order(
    session, database, reverse, introduce_alias, later_minutes
):
    original = observation("ALIAS_ORIGINAL")
    synchronize(database, [batch(original)], checked_at=NOW)
    stored = session.scalar(select(Race))
    race_id, scope_ids = stored.id, [scope.id for scope in stored.scopes]
    corrected = observation("ALIAS_CORRECTED")
    proof = AliasProof(corrected.key, race_id, original.key, 1, "reviewed-alias-proof", NOW)
    if not introduce_alias:
        assert (
            synchronize(database, [batch(corrected, aliases=(proof,))], checked_at=NOW).status
            == "success"
        )
    original_changed = observation("ALIAS_ORIGINAL", html=HTML.replace("collines", "Alpha"))
    later = NOW + timedelta(minutes=later_minutes)
    alias_changed = observation(
        "ALIAS_CORRECTED", html=HTML.replace("collines", "Beta"), checked=later
    )
    inputs = [
        batch(original_changed),
        batch(alias_changed, checked=later, aliases=(proof,) if introduce_alias else ()),
    ]
    if reverse:
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=later)
    session.expire_all()
    stored = session.get(Race, race_id)
    assert result.status == "failed" and result.missing_marked == 0
    assert stored.name.endswith("collines") and stored.revision == 1
    assert stored.source_presence == "present"
    assert [scope.id for scope in stored.scopes] == scope_ids
    assert count(session, Race) == count(session, SourceRevision) == 1
    assert count(session, SourceAlias) == (1 if introduce_alias else 2)
    items = session.scalars(
        select(ImportItem).join(ImportWindow).where(ImportWindow.run_id == result.run_id)
    ).all()
    assert len(items) == 2
    assert all(
        item.diagnostic == "conflicting_details" and item.status == "review" for item in items
    )


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("introduce_alias", [False, True])
def test_identical_alias_facts_with_different_check_times_are_idempotent(
    session, database, reverse, introduce_alias
):
    original = observation("SAME_ORIGINAL")
    synchronize(database, [batch(original)], checked_at=NOW)
    stored = session.scalar(select(Race))
    corrected = observation("SAME_CORRECTED")
    proof = AliasProof(corrected.key, stored.id, original.key, 1, "same-alias-proof", NOW)
    if not introduce_alias:
        synchronize(database, [batch(corrected, aliases=(proof,))], checked_at=NOW)
    later = NOW + timedelta(minutes=1)
    original_changed = observation(
        "SAME_ORIGINAL", html=HTML.replace("collines", "Updated"), checked=later
    )
    alias_changed = observation("SAME_CORRECTED", html=HTML.replace("collines", "Updated"))
    inputs = [
        batch(original_changed, checked=later),
        batch(alias_changed, aliases=(proof,) if introduce_alias else ()),
    ]
    if reverse:
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=later)
    session.expire_all()
    assert result.status == "success" and result.missing_marked == 0
    stored = session.get(Race, stored.id)
    assert stored.name.endswith("Updated") and stored.revision == 2
    assert stored.source.checked_at == later
    assert count(session, SourceRevision) == 2
    assert count(session, SourceAlias) == 2
    assert synchronize(database, inputs, checked_at=later).status == "success"
    assert count(session, SourceRevision) == 2


def test_alias_conflict_preserves_independent_positive_window_and_prevents_absence(
    session, database
):
    original, missing = observation("CONFLICT_ORIGINAL"), observation("UNSEEN")
    synchronize(database, [batch(original, missing)], checked_at=NOW)
    target = session.scalar(select(Race).where(Race.source.has(race_number="CONFLICT_ORIGINAL")))
    corrected = observation("CONFLICT_CORRECTED")
    proof = AliasProof(corrected.key, target.id, original.key, 1, "conflict-alias-proof", NOW)
    synchronize(database, [batch(corrected, missing, aliases=(proof,))], checked_at=NOW)
    inputs = [
        batch(observation("CONFLICT_ORIGINAL", html=HTML.replace("collines", "Alpha"))),
        batch(observation("CONFLICT_CORRECTED", html=HTML.replace("collines", "Beta"))),
        batch(observation("INDEPENDENT")),
    ]
    result = synchronize(database, inputs, checked_at=NOW)
    session.expire_all()
    assert result.status == "partial" and result.missing_marked == 0
    assert count(session, Race) == count(session, SourceRevision) == 3
    assert session.get(Race, target.id).name.endswith("collines")
    assert all(race.source_presence == "present" for race in session.scalars(select(Race)))


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("same_facts", [False, True])
def test_two_new_proven_aliases_resolve_to_one_baseline_before_any_mutation(
    session, database, reverse, same_facts
):
    original = observation("BASELINE")
    synchronize(database, [batch(original)], checked_at=NOW)
    stored = session.scalar(select(Race))
    left = observation("NEW_LEFT", html=HTML.replace("collines", "Alpha"))
    right = observation(
        "NEW_RIGHT", html=HTML.replace("collines", "Alpha" if same_facts else "Beta")
    )
    left_proof = AliasProof(left.key, stored.id, original.key, 1, "left-proof", NOW)
    right_proof = AliasProof(right.key, stored.id, original.key, 1, "right-proof", NOW)
    inputs = [batch(left, aliases=(left_proof,)), batch(right, aliases=(right_proof,))]
    if reverse:
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=NOW)
    session.expire_all()
    assert result.status == "failed" and result.missing_marked == 0
    assert session.get(Race, stored.id).name.endswith("collines")
    assert count(session, SourceAlias) == count(session, SourceRevision) == 1


@pytest.mark.parametrize("reverse", [False, True])
def test_attested_identical_scope_changes_through_aliases_compare_persistent_bindings(
    session, database, reverse
):
    original = observation("SCOPE_ORIGINAL")
    synchronize(database, [batch(original)], checked_at=NOW)
    stored = session.scalar(select(Race))
    corrected = observation("SCOPE_CORRECTED")
    alias_proof = AliasProof(corrected.key, stored.id, original.key, 1, "scope-alias-proof", NOW)
    synchronize(database, [batch(corrected, aliases=(alias_proof,))], checked_at=NOW)
    later = NOW + timedelta(minutes=1)
    body = HTML.replace("Restriction fictive A", "Restriction fictive B")
    left = observation("SCOPE_ORIGINAL", html=body, checked=later)
    right = observation("SCOPE_CORRECTED", html=body)
    inputs = [
        batch(left, checked=later, identities=(identities(left, stored),)),
        batch(right, identities=(identities(right, stored),)),
    ]
    if reverse:
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=later)
    session.expire_all()
    assert result.status == "success", [
        (item.status, item.diagnostic)
        for item in session.scalars(
            select(ImportItem).join(ImportWindow).where(ImportWindow.run_id == result.run_id)
        )
    ]
    assert session.get(Race, stored.id).revision == 2
    assert count(session, SourceRevision) == 2


def test_competing_proofs_for_one_new_key_do_not_assert_an_arbitrary_audit_owner(session, database):
    left, right = observation("OWNER_LEFT"), observation("OWNER_RIGHT")
    synchronize(database, [batch(left, right)], checked_at=NOW)
    races = {race.source.race_number: race for race in session.scalars(select(Race))}
    new = observation("AMBIGUOUS_NEW_KEY")
    proofs = (
        AliasProof(new.key, races["OWNER_LEFT"].id, left.key, 1, "claim-left", NOW),
        AliasProof(new.key, races["OWNER_RIGHT"].id, right.key, 1, "claim-right", NOW),
    )
    result = synchronize(
        database, [batch(new, aliases=(proof,)) for proof in proofs], checked_at=NOW
    )
    assert result.status == "failed" and result.missing_marked == 0
    assert (
        count(session, SourceAlias) == count(session, SourceRevision) == count(session, Race) == 2
    )
    items = session.scalars(
        select(ImportItem).join(ImportWindow).where(ImportWindow.run_id == result.run_id)
    ).all()
    assert all(item.race_id is None and item.diagnostic == "conflicting_details" for item in items)


def seed_controlled_absence(session, database):
    present_time = NOW + timedelta(hours=2)
    original = observation("PRESENCE_ORIGINAL", checked=present_time)
    synchronize(database, [batch(original, checked=present_time)], checked_at=present_time)
    stored = session.scalar(select(Race))
    corrected = observation("PRESENCE_CORRECTED", checked=present_time)
    proof = AliasProof(
        corrected.key, stored.id, original.key, 1, "presence-alias-proof", present_time
    )
    synchronize(
        database,
        [batch(corrected, checked=present_time, aliases=(proof,))],
        checked_at=present_time,
    )
    absence_time = NOW + timedelta(hours=3)
    result = synchronize(database, [batch(checked=absence_time)], checked_at=absence_time)
    session.expire_all()
    assert result.missing_marked == 1
    assert session.get(Race, stored.id).source_presence == "to_verify"
    return stored.id, present_time, absence_time


@pytest.mark.parametrize("offset", [0, 2.5, 3])
@pytest.mark.parametrize("mode", ["single", "aliases", "reversed_aliases"])
def test_historical_or_equal_evidence_cannot_overrule_controlled_absence(
    session, database, offset, mode
):
    race_id, present_time, absence_time = seed_controlled_absence(session, database)
    checked = NOW + timedelta(hours=offset)
    inputs = [batch(observation("PRESENCE_ORIGINAL", checked=checked), checked=checked)]
    if mode != "single":
        inputs.append(batch(observation("PRESENCE_CORRECTED", checked=checked), checked=checked))
    if mode == "reversed_aliases":
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=NOW + timedelta(hours=4))
    session.expire_all()
    stored = session.get(Race, race_id)
    assert result.status == "failed" and result.missing_marked == 0
    assert stored.source_presence == "to_verify"
    assert stored.source.checked_at == present_time
    assert stored.source.presence_checked_at == absence_time
    assert stored.revision == 1 and count(session, SourceRevision) == 1
    items = session.scalars(
        select(ImportItem).join(ImportWindow).where(ImportWindow.run_id == result.run_id)
    ).all()
    assert all(item.status == "error" and item.diagnostic == "stale_observation" for item in items)


@pytest.mark.parametrize("reverse", [False, True])
def test_genuinely_fresh_alias_return_advances_presence_in_both_orders(session, database, reverse):
    race_id, _, _ = seed_controlled_absence(session, database)
    earlier, later = NOW + timedelta(hours=3.5), NOW + timedelta(hours=4)
    inputs = [
        batch(observation("PRESENCE_ORIGINAL", checked=earlier), checked=earlier),
        batch(observation("PRESENCE_CORRECTED", checked=later), checked=later),
    ]
    if reverse:
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=later)
    session.expire_all()
    stored = session.get(Race, race_id)
    assert result.status == "success" and result.missing_marked == 0
    assert stored.source_presence == "present"
    assert stored.source.checked_at == stored.source.presence_checked_at == later
    assert count(session, Race) == count(session, SourceRevision) == 1


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("failure", ["future", "provider", "storage"])
def test_failed_fresh_member_cannot_lend_presence_to_historical_alias(
    session, database, monkeypatch, reverse, failure
):
    race_id, present_time, absence_time = seed_controlled_absence(session, database)
    current = NOW + timedelta(hours=4)
    old = observation("PRESENCE_ORIGINAL")
    fresh = observation(
        "PRESENCE_CORRECTED",
        checked=current if failure != "future" else current + timedelta(hours=1),
    )
    old_batch, fresh_batch = batch(old), batch(fresh, checked=current)
    provider = None
    calls = []
    if failure == "provider":
        old_fact = LocationFact(old.key, "Commune fictive", "26", "source-proof", "26999")
        fresh_fact = replace(old_fact, key=fresh.key)
        old_batch = replace(old_batch, locations=(old_fact,))
        fresh_batch = replace(fresh_batch, locations=(fresh_fact,))

        def fail_provider(_):
            calls.append(1)
            raise RuntimeError("PRIVATE_PROVIDER_FAILURE")

        provider = OfflineProvider("offline-failed-fresh", "v1", fail_provider)
    if failure == "storage":
        from raceatlas.sync import service

        real_apply = service._apply

        def fail_storage(session, observed, *args, **kwargs):
            if observed.key == fresh.key:
                observed = replace(observed, name=None)
            return real_apply(session, observed, *args, **kwargs)

        monkeypatch.setattr(service, "_apply", fail_storage)
    inputs = [old_batch, fresh_batch]
    if reverse:
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=current, provider=provider)
    session.expire_all()
    stored = session.get(Race, race_id)
    assert result.status == "failed" and result.missing_marked == 0
    assert stored.source_presence == "to_verify"
    assert stored.source.checked_at == present_time
    assert stored.source.presence_checked_at == absence_time
    assert count(session, SourceRevision) == 1 and count(session, SourceAlias) == 2
    if failure == "provider":
        assert len(calls) == 1
        assert count(session, GeocodeCache) == 1


def test_historical_source_cannot_add_alias_or_geocode_proof(session, database):
    race_id, present_time, absence_time = seed_controlled_absence(session, database)
    old_time = NOW + timedelta(hours=2.5)
    old = observation("HISTORICAL_UNREGISTERED", checked=old_time)
    expected_key = SourceKey(2027, "PRESENCE_CORRECTED")
    proof = AliasProof(old.key, race_id, expected_key, 1, "historical-proof", old_time)
    fact = LocationFact(old.key, "Commune fictive", "26", "historical-location-proof", "26999")
    calls = []
    provider = OfflineProvider("historical-provider", "v1", lambda _: calls.append(1))
    result = synchronize(
        database,
        [batch(old, checked=old_time, aliases=(proof,), locations=(fact,))],
        checked_at=NOW + timedelta(hours=4),
        provider=provider,
    )
    session.expire_all()
    stored = session.get(Race, race_id)
    assert result.status == "failed" and stored.source_presence == "to_verify"
    assert (
        stored.source.presence_checked_at == absence_time
        and stored.source.checked_at == present_time
    )
    assert calls == [] and count(session, GeocodeCache) == 0
    assert count(session, SourceAlias) == 2 and stored.commune_id is None


def test_repeated_controlled_absence_advances_evidence_without_fabricating_revision(
    session, database
):
    race_id, present_time, _ = seed_controlled_absence(session, database)
    repeated = NOW + timedelta(hours=3.5)
    result = synchronize(database, [batch(checked=repeated)], checked_at=repeated)
    session.expire_all()
    stored = session.get(Race, race_id)
    assert result.status == "success" and result.missing_marked == 0
    assert stored.source_presence == "to_verify"
    assert (
        stored.source.presence_checked_at == repeated and stored.source.checked_at == present_time
    )
    observed = observation("PRESENCE_ORIGINAL", checked=NOW + timedelta(hours=3.25))
    assert (
        synchronize(
            database,
            [batch(observed, checked=observed.checked_at)],
            checked_at=NOW + timedelta(hours=4),
        ).status
        == "failed"
    )
    assert count(session, SourceRevision) == 1


def test_presence_marker_database_constraint_preserves_page_freshness(session, database):
    from sqlalchemy.exc import IntegrityError

    synchronize(database, [batch(observation())], checked_at=NOW)
    with pytest.raises(IntegrityError):
        session.execute(
            text("UPDATE source_record SET presence_checked_at=checked_at - interval '1 second'")
        )
        session.commit()
    session.rollback()


def test_presence_marker_migration_backfills_real_audit_and_repairs_legacy_false_presence(
    session, database
):
    from alembic import command
    from alembic.config import Config

    race_id, _, absence_time = seed_controlled_absence(session, database)
    session.close()
    config = Config(str(ROOT / "alembic.ini"))
    command.downgrade(config, "65107930ec01")
    try:
        with database.begin() as connection:
            connection.execute(
                text("UPDATE race SET source_presence='present' WHERE id=:id"), {"id": race_id}
            )
            connection.execute(
                text("UPDATE source_record SET checked_at=:checked WHERE race_id=:id"),
                {"id": race_id, "checked": NOW + timedelta(hours=2.5)},
            )
    finally:
        command.upgrade(config, "head")
    command.check(config)
    with Session(database) as review:
        restored = review.get(Race, race_id)
        assert restored.source.presence_checked_at == absence_time
        assert restored.source_presence == "to_verify"


def test_presence_marker_migration_does_not_backfill_absence_when_any_alias_window_is_positive(
    session, database
):
    from alembic import command
    from alembic.config import Config

    original = observation("MIGRATION_ORIGINAL")
    synchronize(database, [batch(original)], checked_at=NOW)
    stored = session.scalar(select(Race))
    corrected = observation("MIGRATION_ALIAS")
    proof = AliasProof(corrected.key, stored.id, original.key, 1, "migration-alias-proof", NOW)
    synchronize(database, [batch(corrected, aliases=(proof,))], checked_at=NOW)
    later = NOW + timedelta(hours=1)
    positive = observation("MIGRATION_ALIAS", checked=later)
    assert (
        synchronize(
            database, [batch(checked=later), batch(positive, checked=later)], checked_at=later
        ).status
        == "success"
    )
    race_id = stored.id
    session.close()
    config = Config(str(ROOT / "alembic.ini"))
    command.downgrade(config, "65107930ec01")
    command.upgrade(config, "head")
    command.check(config)
    with Session(database) as review:
        restored = review.get(Race, race_id)
        assert restored.source_presence == "present"
        assert restored.source.presence_checked_at == later


def test_equal_time_migration_absence_is_conservative_without_tainting_unrelated_presence(
    session, database
):
    from alembic import command
    from alembic.config import Config

    race_id, _, absence_time = seed_controlled_absence(session, database)
    legitimate = observation(
        "LEGITIMATE_NO_ABSENCE",
        html=HTML.replace("<dd>26</dd>", "<dd>38</dd>"),
        checked=absence_time,
    )
    legitimate_batch = batch(legitimate, checked=absence_time)
    legitimate_batch = replace(
        legitimate_batch,
        calendar=replace(
            legitimate_batch.calendar,
            requested=replace(WINDOW, department="38"),
            effective_department="38",
        ),
    )
    assert synchronize(database, [legitimate_batch], checked_at=absence_time).status == "success"
    legitimate_id = session.scalar(
        select(Race.id).where(Race.source.has(race_number="LEGITIMATE_NO_ABSENCE"))
    )
    session.close()
    config = Config(str(ROOT / "alembic.ini"))
    command.downgrade(config, "65107930ec01")
    try:
        with database.begin() as connection:
            connection.execute(
                text("UPDATE source_record SET checked_at=:checked WHERE race_id=:id"),
                {"id": race_id, "checked": absence_time},
            )
            connection.execute(
                text("UPDATE race SET source_presence='present' WHERE id=:id"), {"id": race_id}
            )
    finally:
        command.upgrade(config, "head")
    command.check(config)
    with Session(database) as review:
        absent = review.get(Race, race_id)
        positive = review.get(Race, legitimate_id)
        assert absent.source.checked_at == absent.source.presence_checked_at == absence_time
        assert absent.source_presence == "to_verify"
        assert positive.source_presence == "present"
        assert positive.source.checked_at == positive.source.presence_checked_at == absence_time


@pytest.mark.parametrize("reverse", [False, True])
def test_prebaseline_duplicate_is_nonauthoritative_until_actual_fresh_return_succeeds(
    session, database, reverse
):
    race_id, _, _ = seed_controlled_absence(session, database)
    fresh_time = NOW + timedelta(hours=4)
    old = observation("PRESENCE_ORIGINAL")
    fresh = observation("PRESENCE_CORRECTED", checked=fresh_time)
    inputs = [batch(old), batch(fresh, checked=fresh_time)]
    if reverse:
        inputs.reverse()
    result = synchronize(database, inputs, checked_at=fresh_time)
    session.expire_all()
    stored = session.get(Race, race_id)
    assert result.status == "success" and stored.source_presence == "present"
    assert stored.source.checked_at == stored.source.presence_checked_at == fresh_time
    item = session.scalar(
        select(ImportItem)
        .join(ImportWindow)
        .where(ImportWindow.run_id == result.run_id, ImportItem.race_number == "PRESENCE_ORIGINAL")
    )
    assert item.status == "unchanged" and item.diagnostic == "historical_duplicate"
    assert count(session, SourceRevision) == 1
