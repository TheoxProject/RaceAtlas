import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from raceatlas import create_app
from raceatlas.models import Category, EntryScope, Race
from raceatlas.seed import seed_synthetic

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts/catalog.schema.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "fixtures/catalog.v1.json").read_text(encoding="utf-8"))


def validate(document, definition):
    schema = {"$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{definition}"}
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)


def test_all_seeded_details_preserve_contract(seeded, app):
    client = app.test_client()
    for expected in CATALOG["races"]:
        response = client.get(f"/api/v1/races/{expected['id']}")
        assert response.status_code == 200
        actual = response.get_json()
        validate(actual, "Race")
        # Types are a set in the contract; relational rows return stable code order.
        expected = dict(expected, types=sorted(expected["types"]))
        assert actual == expected
    assert client.get("/api/health/live").json == {"status": "ok"}
    assert client.get("/api/health/ready").status_code == 200


def test_seed_idempotent_and_identity_stable(seeded):
    race = seeded.get(Race, "race-road-combined")
    scope_ids = [scope.id for scope in race.scopes]
    race.name = "Titre révisé"
    race.competition_id = None
    seeded.commit()
    assert seed_synthetic(seeded) == 0
    seeded.commit()
    assert seeded.scalar(select(func.count()).select_from(Race)) == len(CATALOG["races"])
    assert seeded.get(Race, race.id).name == "Titre révisé"
    assert [scope.id for scope in race.scopes] == scope_ids
    assert seeded.scalar(select(func.count()).select_from(Category)) == len(CATALOG["categories"])
    assert seeded.scalar(select(func.count()).select_from(EntryScope)) == sum(
        len(race["entry_scopes"]) for race in CATALOG["races"]
    )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE race SET end_date = start_date - 1 WHERE id = 'race-road-combined'",
        "UPDATE race SET discipline = 'clm' WHERE id = 'race-road-combined'",
        "UPDATE race SET discipline = 'gravel' WHERE id = 'race-road-combined'",
        "UPDATE race SET department = '75' WHERE id = 'race-road-combined'",
        "UPDATE race SET department = '01' WHERE id = 'race-road-combined'",
        "UPDATE race SET competition_id = 'absent' WHERE id = 'race-road-combined'",
        "UPDATE race SET status = 'invented' WHERE id = 'race-road-combined'",
        "UPDATE source_record SET race_number = 'SYN-race-road-combined' "
        "WHERE race_id = 'race-road-split'",
        "INSERT INTO rule_category(rule_id,category_code,position) "
        "VALUES ('rule-combined','open_1',99)",
        "INSERT INTO rule_category(rule_id,category_code,position) "
        "VALUES ('rule-combined','not_a_category',99)",
        "UPDATE eligibility_rule SET min_age = 120, max_age = 18 WHERE id = 'rule-combined'",
        "UPDATE commune SET longitude = 181 WHERE id = 'commune-synthetic-a'",
        "UPDATE commune SET latitude = NULL WHERE id = 'commune-synthetic-a'",
        "INSERT INTO race_type(race_id,discipline,code) "
        "VALUES ('race-gravel','gravel','time_trial')",
    ],
)
def test_postgresql_rejects_invalid_business_data(seeded, statement):
    with pytest.raises(IntegrityError):
        seeded.execute(text(statement))
        seeded.commit()
    seeded.rollback()


def test_errors_empty_and_no_api_spa_fallback(session, app):
    client = app.test_client()
    assert client.get("/api/foundation/demo").json == {"synthetic": True, "race_id": None}
    for path in ("/api/v1/races/absent", "/api/v1/races", "/api/v1/map", "/api/absent"):
        response = client.get(path)
        assert response.status_code == 404
        validate(response.json, "Error")
        assert response.headers["X-Request-ID"] == response.json["request_id"]
    response = client.get("/assets/../../README.md")
    assert response.status_code == 404


def test_database_unavailable_has_safe_error(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://wrong:private@127.0.0.1:1/absent")
    app = create_app({"TESTING": True})
    try:
        client = app.test_client()
        assert client.get("/api/health/live").status_code == 200
        for path in ("/api/health/ready", "/api/foundation/demo", "/api/v1/races/absent"):
            response = client.get(path)
            assert response.status_code == 503
            validate(response.json, "Error")
            assert "private" not in response.text and "psycopg" not in response.text
    finally:
        app.extensions["database"].dispose()


def test_production_disables_synthetic_seed(database, monkeypatch):
    monkeypatch.setenv("RACEATLAS_ENV", "production")
    app = create_app()
    try:
        result = app.test_cli_runner().invoke(args=["seed-synthetic"])
        assert result.exit_code != 0
        assert "disabled in production" in result.output
    finally:
        app.extensions["database"].dispose()


def test_configuration_fails_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        create_app()
