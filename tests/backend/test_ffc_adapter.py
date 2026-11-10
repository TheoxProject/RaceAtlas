import json
from dataclasses import asdict, replace
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from raceatlas.ffc import (
    AdapterError,
    IdentityAttestation,
    WindowRequest,
    parse_calendar,
    parse_race,
    project_race,
)
from raceatlas.models import Category
from raceatlas.serialization import race_document

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures/ffc"
RACE_HTML = (FIXTURES / "race.synthetic.html").read_text(encoding="utf-8")
CALENDAR_HTML = (FIXTURES / "calendar.synthetic.html").read_text(encoding="utf-8")
URL = "https://competitions.ffc.fr/calendrier/competition/2027/SYNTHETIC001/access-clm/"
CALENDAR_URL = "https://competitions.ffc.fr/calendrier/"
CHECKED = datetime(2026, 11, 10, 16, tzinfo=timezone.utc)
WINDOW = WindowRequest(date(2026, 11, 10), date(2026, 11, 16), "26")


def race(html=RACE_HTML, url=URL, checked=CHECKED):
    return parse_race(html, source_url=url, checked_at=checked)


def calendar(html=CALENDAR_HTML, requested=WINDOW):
    return parse_calendar(html, source_url=CALENDAR_URL, checked_at=CHECKED, requested=requested)


def validate(document, definition):
    schema = json.loads((ROOT / "contracts/catalog.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(
        {"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"},
        format_checker=FormatChecker(),
    ).validate(document)


def attestation(observation, existing):
    return IdentityAttestation(
        observation.key,
        existing.id,
        "review-proof-synthetic",
        tuple(
            (scope.token, previous.id)
            for scope, previous in zip(observation.scopes, existing.scopes, strict=True)
        ),
        tuple(
            (rule.token, old.id)
            for scope, previous in zip(observation.scopes, existing.scopes, strict=True)
            for rule, old in zip(scope.rules, previous.rules, strict=True)
        ),
    )


def test_calendar_deduplicates_source_keys_ignores_slug_and_keeps_seasons():
    observation = calendar()
    assert [(key.season, key.race_number) for key in observation.keys] == [
        (2026, "SYNTHETIC002"),
        (2027, "SYNTHETIC001"),
    ]
    assert observation.status == "consistent_sample"
    assert not observation.diagnostics
    validate(observation.window_document(), "Window")


@pytest.mark.parametrize(
    "before,after,code",
    [
        ('value="2026-11-10"', 'value="2026-11-11"', "window_mismatch"),
        ('value="26" selected', 'value="38" selected', "department_mismatch"),
        ("2 épreuves", "3 épreuves", "count_mismatch"),
    ],
)
def test_inconsistent_windows_are_incomplete(before, after, code):
    observation = calendar(CALENDAR_HTML.replace(before, after))
    assert observation.status == "incomplete"
    assert code in [item.code for item in observation.diagnostics]
    validate(observation.window_document(), "Window")


def test_empty_calendar_is_observation_only_never_a_cancellation():
    html = CALENDAR_HTML[: CALENDAR_HTML.index("<a href=")] + "</body></html>"
    observation = calendar(html.replace("2 épreuves", "0 épreuve"))
    assert observation.keys == ()
    assert observation.status == "consistent_sample"
    assert "cancelled" not in repr(observation)


@pytest.mark.parametrize(
    "html,code",
    [
        (CALENDAR_HTML.replace("InfoJourSelection", "changed"), "layout_changed"),
        (CALENDAR_HTML.replace('value="7" selected', 'value="28" selected'), "invalid_window"),
        (CALENDAR_HTML.replace("2026-11-10", "2026-02-30"), "invalid_date"),
        (CALENDAR_HTML.replace("/competition/2027/", "/competition/1999/"), "invalid_source_key"),
        (
            CALENDAR_HTML.replace('href="/calendrier', 'href="https://evil.invalid/calendrier'),
            "invalid_source_url",
        ),
    ],
)
def test_calendar_drift_and_invalid_facts_fail(html, code):
    with pytest.raises(AdapterError) as error:
        calendar(html)
    assert error.value.diagnostic.code == code


def test_invalid_requested_window_is_not_silently_repaired():
    for window in (
        WindowRequest(date(2026, 11, 16), date(2026, 11, 10), "26"),
        WindowRequest(date(2026, 11, 1), date(2026, 11, 30), "26"),
        WindowRequest(date(2026, 11, 10), date(2026, 11, 16), "75"),
    ):
        with pytest.raises(AdapterError):
            calendar(requested=window)


def test_race_restrictions_scopes_and_source_season_are_independent():
    observation = race()
    assert observation.key.season == 2027
    assert observation.start_date.year == 2026
    assert observation.discipline == "road"
    assert observation.types == ("time_trial",)
    first, second = observation.scopes
    assert first.rules[0].category_codes == ("open_1",)
    assert first.rules[0].restrictions.sex == "men"
    assert first.rules[0].restrictions.age_season == 2027
    assert first.rules[0].restrictions.engagers == ("Club",)
    assert first.rules[0].restrictions.other_text == "Restriction fictive A"
    assert first.rules[1].category_codes == ("open_2",)
    assert first.rules[1].restrictions.sex == "women"
    assert first.rules[1].restrictions.age_reference == "event_date"
    assert second.rules[0].category_codes == ("access_1", "access_2", "access_3", "access_4")
    assert all(scope.source_list_id is None for scope in observation.scopes)
    assert all(scope.identity_status == "unverified" for scope in observation.scopes)
    assert "PRIVATE_SENTINEL" not in repr(asdict(observation))
    assert "<html" not in repr(asdict(observation))
    assert observation.normalization_version == "ffc-observation-1.0.0"


def test_no_sport_or_eligibility_inferred_from_slug_or_list_id():
    html = RACE_HTML.replace("<dt>Type sportif</dt><dd>CLM</dd>", "")
    observation = race(html, URL.replace("access-clm", "open-1-open-2-access-1-2-3-4-clm"))
    assert observation.types == ()
    assert observation.scopes[0].source_list_id is None  # id=liste-1 is not evidence
    assert observation.scopes[0].rules[0].category_codes == ("open_1",)


@pytest.mark.parametrize("label", ["Access", "Open", "Access 1 / Open 1", "Catégorie inconnue"])
def test_generic_and_unknown_categories_never_confirm_or_expand(label):
    observation = race(RACE_HTML.replace("<dd>Open 1</dd>", f"<dd>{label}</dd>"))
    scope = observation.scopes[0]
    assert scope.eligibility_status == "ambiguous"
    assert all("open_1" not in rule.category_codes for rule in scope.rules)
    assert label in scope.raw_label
    assert any(item.code == "unknown_category" for item in observation.diagnostics)


def test_unknown_restriction_does_not_confirm_known_categories():
    html = RACE_HTML.replace("<dt>Sexe</dt><dd>Hommes</dd>", "<dt>Licence spéciale</dt><dd>X</dd>")
    observation = race(html)
    assert observation.scopes[0].eligibility_status == "ambiguous"
    assert all("open_1" not in rule.category_codes for rule in observation.scopes[0].rules)
    assert "Licence spéciale" in observation.scopes[0].raw_label


@pytest.mark.parametrize(
    "before,after,code",
    [
        ("<dd>Route</dd>", "<dd>CLM</dd>", "unknown_discipline"),
        ("<dd>Route</dd>", "<dd>Gravel</dd>", "incompatible_type"),
        ("2026-11-11", "2026-02-30", "invalid_date"),
        ("<dd>26</dd>", "<dd>75</dd>", "invalid_department"),
        ("<dd>18</dd>", "<dd>inconnu</dd>", "invalid_restriction"),
        ('id="raceDetails"', 'id="changed"', "layout_changed"),
        ("<dt>Discipline</dt><dd>Route</dd>", "", "missing_field"),
        (
            "<dt>Discipline</dt><dd>Route</dd>",
            "<dt>Discipline</dt><dd>Route</dd><dt>Discipline</dt><dd>VTT</dd>",
            "duplicate_field",
        ),
        ('class="epreuve"', 'class="changed"', "layout_changed"),
    ],
)
def test_required_facts_and_html_drift_are_explicit_errors(before, after, code):
    with pytest.raises(AdapterError) as error:
        race(RACE_HTML.replace(before, after))
    assert error.value.diagnostic.code == code
    assert "PRIVATE_SENTINEL" not in str(error.value)


def test_no_lists_is_explicit_unknown_scope_and_not_slug_eligibility():
    html = RACE_HTML[: RACE_HTML.index('<div id="epreuvesDiv"')]
    html += '<div id="epreuvesContenu"></div></body></html>'
    observation = race(html)
    assert len(observation.scopes) == 1
    assert observation.scopes[0].eligibility_status == "unknown"
    assert not observation.scopes[0].rules
    assert any(item.code == "unknown_eligibility" for item in observation.diagnostics)


def test_missing_optional_values_stay_unknown_and_status_requires_source():
    html = RACE_HTML.replace("<dt>Organisateur</dt><dd>Club fictif</dd>", "")
    html = html.replace("<dt>Statut</dt><dd>Programmée</dd>", "")
    observation = race(html)
    assert observation.organizer is None
    assert observation.status == "unknown"
    model = project_race(observation)
    assert model.commune_id is None
    assert model.source_presence == "present"
    assert race(RACE_HTML.replace("Programmée", "Annulée")).status == "cancelled"


def test_urls_and_timestamp_do_not_accept_credentials_other_hosts_or_naive_time():
    for url in (
        URL.replace("https://", "http://"),
        URL.replace("competitions.ffc.fr", "competitions.ffc.fr.evil.invalid"),
        URL.replace("https://", "https://user:password@"),
        URL.replace("SYNTHETIC001", "%2F"),
    ):
        with pytest.raises(AdapterError):
            race(url=url)
    with pytest.raises(AdapterError, match="invalid_timestamp"):
        race(checked=datetime(2026, 11, 10))


def test_html_is_bounded_and_never_best_effort_repairs_missing_tags():
    for html in (RACE_HTML.replace("</dl>", "", 1), "x" * 2_000_001):
        with pytest.raises(AdapterError):
            race(html)


def test_new_graph_has_opaque_ids_no_provider_list_id_and_matches_race_schema():
    model = project_race(race())
    UUID(model.id)
    for scope in model.scopes:
        UUID(scope.id)
        assert scope.source_list_id is None
        for rule in scope.rules:
            UUID(rule.id)
    validate(race_document(model), "Race")


def test_revisions_require_attestation_even_with_identical_labels_or_reordered_lists():
    original = project_race(race())
    changed = race(RACE_HTML.replace("Course fictive des collines", "Titre modifié"))
    for observation in (changed, replace(changed, scopes=tuple(reversed(changed.scopes)))):
        with pytest.raises(AdapterError, match="identity_needs_review"):
            project_race(observation, existing=original)
    assert original.name == "Course fictive des collines"
    proof = attestation(changed, original)
    revised = project_race(changed, existing=original, attestation=proof)
    assert revised.id == original.id
    assert [scope.id for scope in revised.scopes] == [scope.id for scope in original.scopes]
    assert [[rule.id for rule in scope.rules] for scope in revised.scopes] == [
        [rule.id for rule in scope.rules] for scope in original.scopes
    ]
    assert revised.name == "Titre modifié"
    assert original.name == "Course fictive des collines"  # detached, no writes


def test_partial_duplicate_or_foreign_identity_attestations_are_rejected():
    observation = race()
    existing = project_race(observation)
    proof = attestation(observation, existing)
    for invalid in (
        replace(proof, evidence_id=""),
        replace(proof, race_id="other-race"),
        replace(proof, scope_ids=proof.scope_ids[:1]),
        replace(proof, scope_ids=(proof.scope_ids[0], proof.scope_ids[0])),
    ):
        with pytest.raises(AdapterError, match="identity_needs_review"):
            project_race(observation, existing=existing, attestation=invalid)
    # Mapping order has no semantic role; tokens, never rank, identify observations.
    reordered = replace(proof, rule_ids=tuple(reversed(proof.rule_ids)))
    assert project_race(observation, existing=existing, attestation=reordered).id == existing.id


def test_source_aliases_and_stale_observations_require_separate_review():
    observation = race()
    existing = project_race(observation)
    changed = race(url=URL.replace("2027", "2028"))
    with pytest.raises(AdapterError, match="identity_needs_review"):
        project_race(changed, existing=existing, attestation=attestation(changed, existing))
    old = replace(observation, checked_at=CHECKED.replace(year=2025))
    with pytest.raises(AdapterError, match="stale_observation"):
        project_race(old, existing=existing, attestation=attestation(old, existing))


def test_historical_cancellation_not_overwritten_by_unknown_status():
    existing = project_race(race(RACE_HTML.replace("Programmée", "Annulée")))
    observation = race(RACE_HTML.replace("<dt>Statut</dt><dd>Programmée</dd>", ""))
    revised = project_race(
        observation, existing=existing, attestation=attestation(observation, existing)
    )
    assert revised.status == "cancelled"


def test_fixture_adapter_postgresql_flask_contract(session, app):
    observation = race()
    model = project_race(observation)
    codes = {
        code for scope in observation.scopes for rule in scope.rules for code in rule.category_codes
    }
    session.add_all(Category(code=code, label=code) for code in codes)
    session.flush()
    session.add(model)
    session.commit()
    response = app.test_client().get(f"/api/v1/races/{model.id}")
    assert response.status_code == 200
    document = response.json
    validate(document, "Race")
    assert document["source"]["source_season"] == 2027
    assert document["start_date"] == "2026-11-11"
    assert document["types"] == ["time_trial"]
    assert document["location"] is None
    assert len(document["entry_scopes"]) == 2
    assert document["entry_scopes"][0]["rules"][0]["restrictions"]["sex"] == "men"
    assert document["entry_scopes"][0]["rules"][1]["restrictions"]["sex"] == "women"
    assert "PRIVATE_SENTINEL" not in response.text


def test_conflicting_canonical_source_identity_is_rejected():
    html = RACE_HTML.replace(
        "<body>",
        '<head><link rel="canonical" href="' + URL.replace("2027", "2028") + '"></head><body>',
    )
    with pytest.raises(AdapterError, match="conflicting_source_key"):
        race(html)


@pytest.mark.parametrize(
    "before,after",
    [
        ("<dt>Organisateur</dt><dd>Club fictif</dd>", ""),
        ("<dt>Type sportif</dt><dd>CLM</dd>", ""),
        ("<dt>Sexe</dt><dd>Hommes</dd>", ""),
        ("<dt>Engageur</dt><dd>Club</dd>", ""),
        ("<dt>Autres restrictions</dt><dd>Restriction fictive A</dd>", ""),
    ],
)
def test_attestation_cannot_erase_known_facts_with_unknown_partial_revision(before, after):
    existing = project_race(race())
    observation = race(RACE_HTML.replace(before, after))
    with pytest.raises(AdapterError, match="incomplete_revision"):
        project_race(observation, existing=existing, attestation=attestation(observation, existing))
    assert existing.organizer == "Club fictif"
    assert existing.types[0].code == "time_trial"


def test_attested_revision_preserves_known_provider_list_identity():
    existing = project_race(race())
    existing.scopes[0].source_list_id = "previously-attested-source-list"
    existing.scopes[0].identity_status = "verified"
    observation = race()
    revised = project_race(
        observation, existing=existing, attestation=attestation(observation, existing)
    )
    assert revised.scopes[0].source_list_id == existing.scopes[0].source_list_id
    assert revised.scopes[0].identity_status == "verified"


@pytest.mark.parametrize(
    "discipline,sport_type,expected_discipline,expected_type",
    [
        ("Route", "Course en ligne", "road", "road_race"),
        ("Gravel", "Gravel", "gravel", "gravel_race"),
        ("VTT", "XCO", "mtb", "xco"),
        ("VTT", "Enduro", "mtb", "enduro"),
        ("VTT", "Descente", "mtb", "downhill"),
        ("Cyclo-cross", "Cyclo-cross", "cyclocross", "cyclocross"),
    ],
)
def test_explicit_supported_sports(discipline, sport_type, expected_discipline, expected_type):
    observation = race(
        RACE_HTML.replace("<dd>Route</dd>", f"<dd>{discipline}</dd>").replace(
            "<dd>CLM</dd>", f"<dd>{sport_type}</dd>"
        )
    )
    assert observation.discipline == expected_discipline
    assert observation.types == (expected_type,)


def test_unknown_sport_type_remains_empty_with_diagnostic():
    observation = race(RACE_HTML.replace("<dd>CLM</dd>", "<dd>Format non établi</dd>"))
    assert observation.types == ()
    assert any(item.code == "unknown_type" for item in observation.diagnostics)


def test_malformed_urls_have_structured_diagnostics():
    with pytest.raises(AdapterError, match="invalid_source_url"):
        race(url="https://[invalid")
    with pytest.raises(AdapterError, match="invalid_source_url"):
        calendar(CALENDAR_HTML.replace('href="/calendrier', 'href="https://[invalid/calendrier'))


def test_rule_attestation_cannot_transfer_rules_between_scopes():
    observation = race()
    existing = project_race(observation)
    proof = attestation(observation, existing)
    first_token, first_id = proof.rule_ids[0]
    last_token, last_id = proof.rule_ids[-1]
    crossed = replace(
        proof, rule_ids=((first_token, last_id), proof.rule_ids[1], (last_token, first_id))
    )
    with pytest.raises(AdapterError, match="Rules cannot move across scopes"):
        project_race(observation, existing=existing, attestation=crossed)


@pytest.mark.parametrize(
    "anchor",
    [
        "<h3>Liste fictive A</h3>",
        '<dl class="regle">',
        '<dl id="raceDetails">',
        '<div id="epreuvesContenu">',
    ],
)
@pytest.mark.parametrize(
    "restriction",
    [
        "Réservé aux titulaires de la licence spéciale X",
        "<p>Réservé aux titulaires de la licence spéciale X</p>",
        "<div><p>Réservé aux titulaires de la licence spéciale X</p></div>",
    ],
)
def test_unrecognized_restrictions_in_semantic_containers_fail_before_confirmation(
    anchor, restriction
):
    with pytest.raises(AdapterError) as error:
        race(RACE_HTML.replace(anchor, anchor + restriction, 1))
    assert error.value.diagnostic.code == "layout_changed"
    assert "licence spéciale" not in str(error.value)


@pytest.mark.parametrize("tag", ["span", "p", "div", "script"])
def test_nested_unrecognized_fact_markup_fails_conservatively(tag):
    html = RACE_HTML.replace("<dd>Hommes</dd>", f"<dd>Hommes<{tag}>restriction X</{tag}></dd>")
    with pytest.raises(AdapterError, match="layout_changed"):
        race(html)


def test_whitespace_comments_and_external_scripts_do_not_change_source_facts():
    html = RACE_HTML.replace('<dl class="regle">', '<dl class="regle">  \n<!-- comment -->')
    html = html.replace(
        "</body>", '<script>const private_value = "PRIVATE_EXTERNAL";</script></body>'
    )
    observation = race(html)
    assert not observation.diagnostics
    assert observation.scopes[0].eligibility_status == "confirmed"
    assert "PRIVATE_EXTERNAL" not in repr(observation)


def test_calendar_end_beyond_date_max_is_structured_error():
    html = CALENDAR_HTML.replace("2026-11-10", "9999-12-31")
    with pytest.raises(AdapterError) as error:
        calendar(html)
    assert error.value.diagnostic.code == "invalid_window"
    assert error.value.diagnostic.field == "effective_end"


def test_calendar_window_ending_exactly_date_max_is_supported():
    html = CALENDAR_HTML.replace("2026-11-10", "9999-12-25")
    requested = WindowRequest(date(9999, 12, 25), date.max, "26")
    observation = calendar(html, requested=requested)
    assert observation.effective_end == date.max
    assert observation.status == "consistent_sample"
    validate(observation.window_document(), "Window")
