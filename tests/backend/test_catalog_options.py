import json
from pathlib import Path

from jsonschema import Draft202012Validator

from raceatlas.models import Category

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts/catalog-options.schema.json").read_text()
)


def test_options_independent_of_races_extensible_and_sorted(session, app):
    session.add_all(
        [Category(code="u15", label="U15"), Category(code="access_1", label="Access 1")]
    )
    session.commit()
    response = app.test_client().get("/api/v1/catalog/options")
    assert response.status_code == 200
    Draft202012Validator(SCHEMA).validate(response.json)
    assert response.json["categories"] == [
        {"code": "access_1", "label": "Access 1"},
        {"code": "u15", "label": "U15"},
    ]
    assert response.headers["Cache-Control"] == "no-store"


def test_options_empty_registry_is_valid(session, app):
    response = app.test_client().get("/api/v1/catalog/options")
    assert response.status_code == 200
    Draft202012Validator(SCHEMA).validate(response.json)
    assert response.json["categories"] == []


def test_options_unavailable_is_public_json(monkeypatch):
    from raceatlas import create_app

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://wrong:private@127.0.0.1:1/absent")
    app = create_app()
    try:
        response = app.test_client().get("/api/v1/catalog/options")
        assert response.status_code == 503 and response.json["code"] == "unavailable"
        assert "private" not in response.text and "SELECT" not in response.text
    finally:
        app.extensions["database"].dispose()
