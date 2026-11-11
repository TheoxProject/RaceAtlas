import json
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import event, text

from raceatlas.models import Category, Race, RuleCategory

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts/catalog.schema.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "fixtures/catalog.v1.json").read_text(encoding="utf-8"))
SCENARIOS = json.loads((ROOT / "fixtures/scenarios.v1.json").read_text(encoding="utf-8"))[
    "scenarios"
]


def validate(document, definition):
    Draft202012Validator(
        {"$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{definition}"}, format_checker=FormatChecker()
    ).validate(document)


def request_page(client, selected=None, *, map_view=False, **params):
    return client.get(
        "/api/v1/map" if map_view else "/api/v1/races",
        query_string={
            "filter": json.dumps(SCENARIOS[0]["filter"] if selected is None else selected),
            **params,
        },
    )


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario["id"])
def test_every_contract_scenario_through_real_postgresql_and_both_endpoints(seeded, app, scenario):
    client = app.test_client()
    page_response = request_page(client, scenario["filter"])
    map_response = request_page(client, scenario["filter"], map_view=True)
    assert page_response.status_code == map_response.status_code == 200
    page, mapped = page_response.json, map_response.json
    validate(page, "RacePage")
    validate(mapped, "MapPage")
    assert {item["race"]["id"] for item in page["items"]} == set(scenario["expected_ids"])
    assert set(mapped["unlocated_ids"]) == set(scenario["expected_unlocated_ids"])
    assert page["unlocated_count"] == len(scenario["expected_unlocated_ids"])
    assert page["total"] == mapped["total"] == len(scenario["expected_ids"])
    assert page["catalog_version"] == mapped["catalog_version"]
    located_expected = {
        race["id"]
        for race in CATALOG["races"]
        if race["id"] in scenario["expected_ids"]
        and race["location"]
        and race["location"]["coordinates"]
    }
    assert {feature["id"] for feature in mapped["features"]} == located_expected
    assert page["next_cursor"] is mapped["next_cursor"] is None
    assert page["coverage"]["status"] == "unknown"  # seed is not a real FFC import
    assert page["coverage"]["intrinsic_exhaustiveness"] == "unknown"


def test_category_and_has_only_same_scope_witnesses_and_keeps_correlated_rules(seeded, app):
    response = request_page(app.test_client(), SCENARIOS[1]["filter"])
    rows = {item["race"]["id"]: item for item in response.json["items"]}
    assert rows["race-correlated"]["matching_scope_ids"] == ["scope-correlated"]
    rules = rows["race-correlated"]["race"]["entry_scopes"][0]["rules"]
    assert len(rules) == 2
    assert {rule["restrictions"]["sex"] for rule in rules} == {"men", "women"}
    assert rows["race-road-combined"]["matching_scope_ids"] == ["scope-road-combined"]
    assert "race-road-split" not in rows and "race-other-one" not in rows


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario["id"])
def test_limit_one_pages_have_shared_cursor_complete_parity_and_stable_order(seeded, app, scenario):
    client = app.test_client()
    cursor, rows, features, unlocated = None, [], [], []
    while True:
        params = {"limit": "1", **({"cursor": cursor} if cursor else {})}
        page = request_page(client, scenario["filter"], **params).json
        mapped = request_page(client, scenario["filter"], map_view=True, **params).json
        validate(page, "RacePage")
        validate(mapped, "MapPage")
        assert page["next_cursor"] == mapped["next_cursor"]
        assert page["total"] == mapped["total"] == len(scenario["expected_ids"])
        assert page["unlocated_count"] == len(scenario["expected_unlocated_ids"])
        rows.extend((item["race"]["start_date"], item["race"]["id"]) for item in page["items"])
        features.extend(feature["id"] for feature in mapped["features"])
        unlocated.extend(mapped["unlocated_ids"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
        assert len(rows) + len(unlocated) < 100
    ids = [row[1] for row in rows]
    assert rows == sorted(rows)
    assert len(ids) == len(set(ids)) == len(scenario["expected_ids"])
    assert set(ids) == set(scenario["expected_ids"])
    assert len(unlocated) == len(set(unlocated)) == len(scenario["expected_unlocated_ids"])
    assert set(unlocated) == set(scenario["expected_unlocated_ids"])
    assert set(features) == set(ids) - set(unlocated)


def test_radius_continues_when_only_unlocated_candidates_remain(seeded, app):
    for race_id in ("race-road-combined", "race-road-split"):
        seeded.get(Race, race_id).commune_id = None
    seeded.commit()
    selected = deepcopy(SCENARIOS[0]["filter"])
    selected["geography"] = {"mode": "radius", "center": [0, 0], "radius_km": 1}
    cursor, candidates = None, []
    for index in range(3):
        params = {"limit": 1, **({"cursor": cursor} if cursor else {})}
        response = request_page(app.test_client(), selected, **params)
        mapped = request_page(app.test_client(), selected, map_view=True, **params).json
        assert response.status_code == 200
        assert response.json["total"] == 0 and response.json["items"] == []
        assert response.json["unlocated_count"] == 3
        assert mapped["features"] == [] and len(mapped["unlocated_ids"]) == 1
        candidates.extend(mapped["unlocated_ids"])
        cursor = response.json["next_cursor"]
        assert cursor == mapped["next_cursor"]
        assert (cursor is None) == (index == 2)
    assert set(candidates) == {"race-road-combined", "race-road-split", "race-unlocated"}


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE race SET name = name WHERE id = 'race-gravel'",
        "UPDATE commune SET name = name",
        "UPDATE source_record SET checked_at = checked_at",
        "UPDATE entry_scope SET raw_label = raw_label",
        "UPDATE eligibility_rule SET raw_label = raw_label",
        "UPDATE rule_category SET position = position",
        "UPDATE race_type SET code = code",
        "UPDATE category SET label = label",
        "UPDATE import_run SET status = status",
        "UPDATE import_window SET status = status",
    ],
)
def test_all_response_affecting_statement_triggers_invalidate_both_cursors(seeded, app, statement):
    client = app.test_client()
    before = request_page(client, limit=1).json
    seeded.execute(text(statement))
    seeded.commit()
    for map_view in (False, True):
        response = request_page(client, map_view=map_view, cursor=before["next_cursor"])
        assert response.status_code == 409
        assert response.json["code"] == "stale_cursor"
    assert request_page(client).json["catalog_version"] != before["catalog_version"]


def test_rollback_does_not_invalidate_and_add_only_seed_stays_readable(seeded, app):
    from raceatlas.seed import seed_synthetic

    client = app.test_client()
    before = request_page(client, limit=1).json
    seeded.execute(text("UPDATE race SET name = 'Rolled back'"))
    seeded.rollback()
    assert request_page(client, cursor=before["next_cursor"]).status_code == 200
    assert seed_synthetic(seeded) == 0
    seeded.commit()
    assert request_page(client).json["catalog_version"] == before["catalog_version"]


def test_registered_category_is_dynamic_and_unknown_category_is_rejected(seeded, app):
    seeded.add(Category(code="u15", label="U15"))
    seeded.flush()
    rule = seeded.get(Race, "race-road-combined").scopes[0].rules[0]
    rule.categories.append(RuleCategory(category_code="u15", position=99))
    seeded.commit()
    selected = deepcopy(SCENARIOS[0]["filter"])
    selected["categories"] = ["u15"]
    response = request_page(app.test_client(), selected)
    assert response.status_code == 200
    assert [item["race"]["id"] for item in response.json["items"]] == ["race-road-combined"]
    selected["categories"] = ["unknown_registered_code"]
    assert request_page(app.test_client(), selected).status_code == 400


@pytest.mark.parametrize("field", ["name", "organizer", "commune"])
def test_normalized_unicode_search_in_each_supported_field_and_literal_wildcards(
    seeded, app, field
):
    race = seeded.get(Race, "race-road-combined")
    target = race.commune if field == "commune" else race
    setattr(target, "name" if field == "commune" else field, "Été\u00a0FÉDÉRÉ 100%_club")
    seeded.commit()
    selected = deepcopy(SCENARIOS[0]["filter"])
    selected["query"] = " e\u0301te  fe\u0301de\u0301re\u0301 100%_club "
    response = request_page(app.test_client(), selected)
    assert response.status_code == 200
    assert "race-road-combined" in {item["race"]["id"] for item in response.json["items"]}
    selected["query"] = "100%_other"
    assert request_page(app.test_client(), selected).json["total"] == 0


def test_inclusive_multiday_and_civil_year_independent_of_source_season(seeded, app):
    race = seeded.get(Race, "race-road-combined")
    race.start_date, race.end_date = date(2026, 12, 31), date(2027, 1, 2)
    race.source.source_season = 2025
    seeded.commit()
    for day in (date(2026, 12, 31), date(2027, 1, 2), date(2027, 1, 3)):
        selected = deepcopy(SCENARIOS[0]["filter"])
        selected.update({"from": day.isoformat(), "to": day.isoformat(), "query": race.name})
        page = request_page(app.test_client(), selected).json
        assert page["total"] == (0 if day == date(2027, 1, 3) else 1)


def test_committed_writer_between_count_and_graph_cannot_mix_snapshot(seeded, app):
    """A separate connection commits while the HTTP read transaction is open."""
    engine = app.extensions["database"]
    client = app.test_client()
    before = request_page(client).json
    changed = False

    def concurrent_write(connection, cursor, statement, parameters, context, executemany):
        nonlocal changed
        if not changed and statement.startswith("SELECT count(*)"):
            changed = True
            with seeded.bind.begin() as writer:
                writer.execute(text("UPDATE race SET name = 'Concurrent committed name'"))
                writer.execute(
                    text(
                        "UPDATE race SET start_date = '2028-01-01', end_date = '2028-01-01' "
                        "WHERE id = 'race-gravel'"
                    )
                )

    event.listen(engine, "after_cursor_execute", concurrent_write)
    try:
        during = request_page(client).json
    finally:
        event.remove(engine, "after_cursor_execute", concurrent_write)
    assert changed
    assert during == before
    after = request_page(client).json
    assert after["catalog_version"] != before["catalog_version"]
    assert after["total"] == before["total"] - 1
    assert all(item["race"]["name"] == "Concurrent committed name" for item in after["items"])
    with engine.connect() as connection:
        assert connection.get_isolation_level() == "READ COMMITTED"
        assert connection.scalar(text("SHOW transaction_read_only")) == "off"


@pytest.mark.parametrize("map_view", [False, True])
@pytest.mark.parametrize(
    "parameters",
    [
        [("filter", "{}"), ("filter", "{}")],
        [("filter", "{}"), ("limit", "1"), ("limit", "2")],
        {"filter": '{"from":"2026-01-01","from":"2027-01-01"}'},
        {"filter": '{"query":NaN}'},
        {"filter": "[" * 1500 + "0" + "]" * 1500},
        {"limit": "201"},
        {"limit": "1.0"},
        {"cursor": "not a cursor"},
        {"cursor": "a" * 4097},
        {"unknown": "SQL_SECRET_SENTINEL"},
        {"filter": json.dumps({**SCENARIOS[0]["filter"], "query": "\ud800"})},
        {"filter": json.dumps({**SCENARIOS[0]["filter"], "query": "\x00"})},
    ],
)
def test_malformed_requests_are_safe_public_schema_errors(seeded, app, map_view, parameters):
    if isinstance(parameters, dict):
        parameters = {"filter": json.dumps(SCENARIOS[0]["filter"]), **parameters}
    response = app.test_client().get(
        "/api/v1/map" if map_view else "/api/v1/races", query_string=parameters
    )
    assert response.status_code == 400
    validate(response.json, "Error")
    assert response.json["code"] == "invalid_filter"
    assert response.json["fields"]
    assert response.json["request_id"] == response.headers["X-Request-ID"]
    assert "SQL_SECRET_SENTINEL" not in response.text
    assert "SELECT " not in response.text and "postgresql" not in response.text


def test_cursor_filter_binding_offset_validation_and_limit_changes(seeded, app):
    from werkzeug.datastructures import MultiDict

    from raceatlas.catalog.cursor import encode_cursor
    from raceatlas.catalog.validation import parse_query

    client = app.test_client()
    before = request_page(client, limit=1).json
    selected = deepcopy(SCENARIOS[0]["filter"])
    selected["query"] = "gravel"
    assert request_page(client, selected, cursor=before["next_cursor"]).status_code == 400
    # Limits may change between requests; the token carries the next stream offset.
    changed_limit = request_page(client, limit=200, cursor=before["next_cursor"])
    assert changed_limit.status_code == 200
    assert len(changed_limit.json["items"]) == before["total"] - 1
    parsed = parse_query(MultiDict({"filter": json.dumps(SCENARIOS[0]["filter"])}))
    out_of_range = encode_cursor(before["catalog_version"], parsed.filter_hash, 2000)
    assert request_page(client, cursor=out_of_range).status_code == 400
