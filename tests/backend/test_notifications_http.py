import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from sqlalchemy import event, select
from test_auth_http_sessions import bootstrap
from test_notifications import ONE, change
from test_private_planning import ORIGIN, actor_client, save, write
from test_private_planning import app as _planning_app
from test_private_planning import isolation as isolation

from raceatlas.models import CatalogState

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
