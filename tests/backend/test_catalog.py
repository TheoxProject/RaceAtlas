import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

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
