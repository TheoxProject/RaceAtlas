import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from sqlalchemy import event, select
from sqlalchemy.exc import SQLAlchemyError
from test_auth_http_sessions import bootstrap
from test_notifications import ONE, change
from test_private_planning import ORIGIN, actor_client, save, write
from test_private_planning import app as _planning_app
from test_private_planning import isolation as isolation

from raceatlas.models import CatalogState
from raceatlas.planning_snapshot import PlanningLimits

BASE = "/api/v1/me/notifications"


@pytest.fixture
def app(database):
    yield from _planning_app.__wrapped__(database)


def test_notification_http_contract_cookie_read_context_and_ack(app, database, seeded):
    client, _ = actor_client(app, database)
    assert save(client, ONE).status_code == 200
    change(seeded, scopes=(ONE,))
    seeded.commit()
    original = seeded.execute(select(CatalogState.epoch, CatalogState.revision)).one()
    page = client.get(BASE + "?limit=1", base_url=ORIGIN)
    assert page.status_code == 200 and page.json["unread_count"] == 1
    assert page.headers["Cache-Control"] == "no-store" and "Set-Cookie" not in page.headers
    registry = Registry()
    contracts = Path(__file__).resolve().parents[2] / "contracts"
    for name in ["notifications.schema.json", "planning.schema.json"]:
        path = contracts / name
        registry = registry.with_resource(
            path.as_uri(), Resource.from_contents(json.loads(path.read_text(encoding="utf-8")))
        )
    Draft202012Validator(
        {"$ref": (contracts / "notifications.schema.json").as_uri()},
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(page.json)
    proof = bootstrap(client)
    linked = client.get(BASE, base_url=ORIGIN, headers={"X-CSRF-Token": proof})
    assert linked.status_code == 200 and linked.json["items"] == page.json["items"]
    acknowledged = write(client, BASE + "/read-all", {}, "post")
    assert acknowledged.status_code == 204 and acknowledged.data == b""
    assert acknowledged.headers["Cache-Control"] == "no-store"
    assert client.get(BASE, base_url=ORIGIN).json["unread_count"] == 0
    assert seeded.execute(select(CatalogState.epoch, CatalogState.revision)).one() == original


@pytest.mark.parametrize(
    "query",
    ["?limit=0", "?limit=101", "?limit=1&limit=2", "?cursor=", "?cursor=bad", "?filter=road"],
)
def test_malformed_notification_query_is_rejected_before_sql(app, query):
    queries = []

    def observe(*_args):
        queries.append(True)

    engine = app.extensions["database"]
    event.listen(engine, "before_cursor_execute", observe)
    try:
        response = app.test_client().get(BASE + query, base_url=ORIGIN)
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    assert response.status_code == 400 and queries == []
    assert "Set-Cookie" not in response.headers


def test_read_proof_cookie_switch_and_mutation_csrf_refused_before_sql(app, database):
    alice, _ = actor_client(app, database)
    bob, _ = actor_client(app, database, "bob@example.test")
    proof = bootstrap(alice)
    settings = app.extensions["auth"].settings
    bob.set_cookie(
        settings.csrf_cookie,
        alice.get_cookie(settings.csrf_cookie, domain="127.0.0.1").value,
        domain="127.0.0.1",
    )
    queries = []

    def observe(*_args):
        queries.append(True)

    engine = app.extensions["database"]
    event.listen(engine, "before_cursor_execute", observe)
    try:
        denied = bob.get(BASE, base_url=ORIGIN, headers={"X-CSRF-Token": proof})
        mutation = alice.post(
            BASE + "/read-all", json={}, base_url=ORIGIN, headers={"Origin": ORIGIN}
        )
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    assert denied.status_code == mutation.status_code == 403 and queries == []
    assert "Set-Cookie" not in denied.headers
    assert alice.get(BASE, base_url=ORIGIN, headers={"X-CSRF-Token": proof}).status_code == 200
    anonymous = app.test_client().get(BASE, base_url=ORIGIN)
    assert anonymous.status_code == 401 and "Set-Cookie" not in anonymous.headers


@pytest.mark.parametrize("failure", [False, True])
def test_notification_session_closed_and_commit_required_before_204(
    app, database, seeded, monkeypatch, failure
):
    import raceatlas.notifications_http as http

    client, _ = actor_client(app, database)
    save(client, ONE)
    change(seeded, scopes=(ONE,))
    seeded.commit()
    proof = bootstrap(client)
    closed = []
    original = http.AccountFlowSession

    class Observed(original):
        def commit(self):
            if failure:
                raise SQLAlchemyError("Synthetic private commit failure")
            return super().commit()

        def close(self):
            result = super().close()
            closed.append(True)
            return result

    monkeypatch.setattr(http, "AccountFlowSession", Observed)
    original_response = app.response_class

    class AfterClose(original_response):
        def __init__(self, *args, **kwargs):
            assert closed, "Private Response created before closing Session"
            super().__init__(*args, **kwargs)

    app.response_class = AfterClose
    response = client.post(
        BASE + "/read-all",
        json={},
        base_url=ORIGIN,
        headers={"Origin": ORIGIN, "X-CSRF-Token": proof},
    )
    app.response_class = original_response
    assert response.status_code == (503 if failure else 204) and closed
    assert "Set-Cookie" not in response.headers
    monkeypatch.setattr(http, "AccountFlowSession", original)
    assert client.get(BASE, base_url=ORIGIN).json["unread_count"] == (1 if failure else 0)


def test_notification_http_wrong_origin_unknown_body_and_explicit_response_limit(
    app, database, seeded
):
    client, _ = actor_client(app, database)
    save(client, ONE)
    change(seeded, scopes=(ONE,))
    seeded.commit()
    proof = bootstrap(client)
    bad_origin = client.post(
        BASE + "/read-all",
        json={},
        base_url=ORIGIN,
        headers={"Origin": "https://different.example.test", "X-CSRF-Token": proof},
    )
    bad_body = write(client, BASE + "/read-all", {"scope_id": ONE}, "post")
    assert bad_origin.status_code == 403 and bad_body.status_code == 400
    app.extensions["notification_limits"] = PlanningLimits(response_bytes=64)
    too_large = client.get(BASE, base_url=ORIGIN)
    assert too_large.status_code == 413 and too_large.json["code"] == "selection_limit"


def test_notification_openapi_refs_are_local_and_routes_are_additive():
    root = Path(__file__).resolve().parents[2] / "contracts"
    document = json.loads((root / "notifications.openapi.json").read_text(encoding="utf-8"))

    def walk(value):
        if isinstance(value, dict):
            if "$ref" in value:
                path, _, pointer = value["$ref"].partition("#")
                # Existing security scheme references use "auth.openapi.json"
                # without a leading ./; both are valid local relative URIs.
                assert (root / path).resolve().parent == root.resolve()
                resolved = json.loads((root / path).read_text(encoding="utf-8"))
                for segment in pointer.split("/")[1:]:
                    resolved = resolved[segment]
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(document)
    assert set(document["paths"]) == {BASE, BASE + "/read-all"}
    assert "204" in document["paths"][BASE + "/read-all"]["post"]["responses"]


def test_native_basic_header_is_not_account_bearer_and_unverified_account_cannot_read(
    app, database
):
    client, _ = actor_client(app, database)
    preview_header = {"Authorization": "Basic c3ludGhldGljOnByZXZpZXc="}
    assert client.get(BASE, base_url=ORIGIN, headers=preview_header).status_code == 200
    anonymous = app.test_client().get(BASE, base_url=ORIGIN, headers=preview_header)
    assert anonymous.status_code == 401 and "Set-Cookie" not in anonymous.headers
    unverified, _ = actor_client(app, database, "unverified@example.test", verified=False)
    assert unverified.get(BASE, base_url=ORIGIN).status_code == 401
