from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from threading import Barrier, Event

import pytest
import requests
import test_sync as source_tests
from sqlalchemy import delete, event, func, select
from sqlalchemy.orm import Session
from test_auth_http_sessions import bootstrap, identity, login

from raceatlas import create_app
from raceatlas.auth.flows import AccountFlowSession
from raceatlas.models import (
    Account,
    AuthAdmissionBucket,
    AuthAdmissionState,
    CatalogState,
    EntryScope,
    Race,
    SavedEntry,
)
from raceatlas.planning import put_saved_entry
from raceatlas.planning_snapshot import PlanningLimits, encode_personal, snapshot_documents
from raceatlas.sync import synchronize
from raceatlas.sync.geocoding import OfflineProvider

ORIGIN = "http://127.0.0.1"
BASE = "/api/v1/me/saved-entries"
OFFLINE = OfflineProvider("planning-offline", "v1", lambda *args: [])


@pytest.fixture(autouse=True)
def isolation(session, database, monkeypatch):
    with database.begin() as connection:
        connection.execute(delete(AuthAdmissionBucket))
        connection.execute(delete(AuthAdmissionState))

    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)


@pytest.fixture
def app(database):
    result = create_app(
        {
            "ENVIRONMENT": "test",
            "DATABASE_URL": database.url,
            "AUTH_ENABLED": True,
            "APP_BASE_URL": ORIGIN,
            "EMAIL_PROVIDER": "development",
            "AUTH_CSRF_KEY": "synthetic-csrf-key-distinct-000000000",
            "AUTH_RATE_KEY": "synthetic-rate-key-distinct-111111111",
        }
    )
    yield result
    assert result.extensions["auth"].close(timeout=5)
    result.extensions["database"].dispose()


def actor_client(app, database, email="alice@example.test", verified=True):
    account_id = identity(database, email, verified=verified)
    client = app.test_client()
    response = login(client, email)
    assert response.status_code == (200 if verified else 401)
    return client, account_id


def write(client, path, body, method="put", **headers):
    return getattr(client, method)(
        path,
        json=body,
        base_url=ORIGIN,
        headers={"Origin": ORIGIN, "X-CSRF-Token": bootstrap(client), **headers},
    )


def save(client, scope, status="interested"):
    return write(client, BASE + "/by-scope/" + scope, {"status": status})


def scopes(session):
    return [scope.id for scope in session.get(Race, "race-road-split").scopes]


def test_private_scopes_crud_noop_revision_two_users_order_and_epoch(app, database, seeded):
    first, alice = actor_client(app, database)
    other, bob = actor_client(app, database, "bob@example.test")
    ids = scopes(seeded)
    epoch = seeded.scalar(select(CatalogState.revision))
    a = save(first, ids[0], "planned")
    b = save(first, ids[1], "registered")
    own_other = save(other, ids[0], "completed")
    assert a.status_code == b.status_code == own_other.status_code == 200
    one, two = a.json["item"], b.json["item"]
    assert one["scope"]["id"] == one["scope_id"] == ids[0]
    assert one["race"]["id"] == two["race"]["id"] and one["scope"] != two["scope"]
    assert (
        "entry_scopes" not in one["race"] and one["race"]["personal_eligibility"] == "not_evaluated"
    )
    assert save(first, ids[0], "planned").json["item"] == one
    changed = write(first, BASE + "/" + one["id"], {"status": "completed"}, "patch")
    assert changed.json["item"]["revision"] == 2 and changed.json["item"]["id"] == one["id"]
    assert (
        write(first, BASE + "/" + one["id"], {"status": "completed"}, "patch").json == changed.json
    )
    response = first.get(BASE, base_url=ORIGIN)
    assert response.status_code == 200 and response.headers["Cache-Control"] == "no-store"
    assert len(response.json["items"]) == 2
    keys = [(item["created_at"], item["id"]) for item in response.json["items"]]
    assert keys == sorted(keys)
    assert len(other.get(BASE, base_url=ORIGIN).json["items"]) == 1
    assert alice not in response.text and bob not in response.text
    assert write(first, BASE + "/" + one["id"], {}, "delete").status_code == 204
    assert len(first.get(BASE, base_url=ORIGIN).json["items"]) == 1
    assert seeded.scalar(select(CatalogState.revision)) == epoch


@pytest.mark.parametrize("method,body", [("patch", {"status": "bogus"}), ("delete", {})])
def test_foreign_and_nonexistent_entries_are_same_404_before_status(
    app, database, seeded, method, body
):
    first, _ = actor_client(app, database)
    other, _ = actor_client(app, database, "bob@example.test")
    foreign = save(other, scopes(seeded)[0]).json["item"]["id"]
    for value in [foreign, "absent", "x" * 65, "nul%00id"]:
        response = write(first, BASE + "/" + value, body, method)
        assert response.status_code == 404 and response.json["code"] == "not_found"
    own = save(first, scopes(seeded)[0]).json["item"]["id"]
    if method == "patch":
        assert write(first, BASE + "/" + own, body, method).status_code == 400


def test_auth_csrf_origin_no_actor_filters_or_calendar_stub(app, database, seeded):
    anonymous = app.test_client()
    assert anonymous.get(BASE, base_url=ORIGIN).status_code == 401
    pending, _ = actor_client(app, database, "pending@example.test", verified=False)
    assert pending.get(BASE, base_url=ORIGIN).status_code == 401
    client, _ = actor_client(app, database)
    target = BASE + "/by-scope/" + scopes(seeded)[0]
    assert (
        write(client, target, {"status": "planned"}, Origin="https://evil.test").status_code == 403
    )
    assert write(client, target, {"status": "planned", "actor_id": "other"}).status_code == 400
    assert client.get(BASE + "?year=2027", base_url=ORIGIN).status_code == 400
    assert client.get("/api/v1/me/calendar.ics", base_url=ORIGIN).status_code == 200
    assert save(client, scopes(seeded)[0]).status_code == 200
    assert (
        client.get(
            BASE, headers={"Authorization": "Basic c3ludGhldGljOnByZXZpZXc="}, base_url=ORIGIN
        ).status_code
        == 200
    )


def test_saved_cap_serializes_new_creations_and_keeps_upserts_removals(app, database, seeded):
    app.extensions["planning_limits"] = PlanningLimits(saved_entries=1)
    client, alice = actor_client(app, database)
    second = app.test_client()
    assert login(second).status_code == 200
    targets = scopes(seeded)
    proofs = [bootstrap(client), bootstrap(second)]
    barrier = Barrier(2)

    def concurrent(c, scope, proof):
        barrier.wait(timeout=5)
        return c.put(
            BASE + "/by-scope/" + scope,
            json={"status": "planned"},
            base_url=ORIGIN,
            headers={"Origin": ORIGIN, "X-CSRF-Token": proof},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(concurrent, c, target, proof)
            for c, target, proof in zip((client, second), targets, proofs, strict=True)
        ]
        results = [future.result(timeout=8) for future in futures]
    assert sorted(response.status_code for response in results) == [200, 413]
    winner = next(response.json["item"] for response in results if response.status_code == 200)
    assert save(client, winner["scope_id"], "registered").status_code == 200
    assert write(client, BASE + "/" + winner["id"], {}, "delete").status_code == 204
    assert save(client, targets[0]).status_code == 200
    with Session(database) as session:
        assert (
            session.scalar(
                select(func.count()).select_from(SavedEntry).where(SavedEntry.account_id == alice)
            )
            == 1
        )


def test_more_than_public_page_no_hidden_filters_or_truncation(app, database, seeded):
    client, alice = actor_client(app, database)
    with Session(database) as session, session.begin():
        for index in range(201):
            scope = EntryScope(
                id=f"private-scope-{index}",
                race_id="race-road-split",
                position=index + 10,
                kind="entry_list",
                identity_status="unverified",
                eligibility_status="unknown",
                raw_label=f"Synthetic scope {index}",
            )
            session.add(scope)
            session.flush()
            session.add(SavedEntry(account_id=alice, scope_id=scope.id, status="interested"))
    response = client.get(BASE, base_url=ORIGIN)
    assert response.status_code == 200 and len(response.json["items"]) == 201
    assert {item["scope"]["raw_label"] for item in response.json["items"]} == {
        f"Synthetic scope {i}" for i in range(201)
    }
    app.extensions["planning_limits"] = PlanningLimits(saved_entries=200)
    assert client.get(BASE, base_url=ORIGIN).status_code == 413


@pytest.mark.parametrize("limit,field", [("text", "scope"), ("bytes", "response")])
def test_resource_bounds_fail_explicitly_and_rollback_new_saved_entry(
    app, database, seeded, limit, field
):
    client, _ = actor_client(app, database)
    if limit == "text":
        scope = seeded.get(EntryScope, scopes(seeded)[0])
        scope.raw_label = "é" * 8193
        seeded.commit()
    else:
        app.extensions["planning_limits"] = PlanningLimits(response_bytes=100)
    response = save(client, scopes(seeded)[0])
    assert response.status_code == 413 and response.json["code"] == "selection_limit"
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(SavedEntry)) == 0


def test_single_graph_select_no_lazy_after_close_and_preloaded_identity_is_refreshed(
    app, database, seeded
):
    _, alice = actor_client(app, database)
    target = scopes(seeded)[0]
    with AccountFlowSession(database) as session:
        actor = session.get(Account, alice)
        put_saved_entry(session, actor, target, "planned")
        session.commit()
        actor = session.get(Account, alice)
        cached = session.get(Race, "race-road-split")
        with Session(database) as writer, writer.begin():
            writer.get(Race, cached.id).name = "Fresh snapshot title"
        queries = []

        def query(*args):
            queries.append(1)

        event.listen(database, "before_cursor_execute", query)
        try:
            docs = snapshot_documents(session, actor)
            assert len(queries) == 1 and cached.name == "Fresh snapshot title"
            session.close()
            before = len(queries)
            data = encode_personal({"items": docs}, PlanningLimits())
            assert len(queries) == before and b"Fresh snapshot title" in data
        finally:
            event.remove(database, "before_cursor_execute", query)


def test_real_import_during_graph_select_cannot_mix_dates_and_scope_labels(app, database, session):
    first = source_tests.observation()
    assert (
        synchronize(
            database, [source_tests.batch(first)], checked_at=source_tests.NOW, provider=OFFLINE
        ).status
        == "success"
    )
    stored = session.scalar(select(Race))
    race_id = stored.id
    proof = source_tests.identities(first, stored)
    scope_id = stored.scopes[0].id
    client, _ = actor_client(app, database)
    initial = save(client, scope_id, "planned").json["item"]
    later = source_tests.NOW + timedelta(hours=1)
    changed_scopes = tuple(
        replace(scope, raw_label=scope.raw_label + " Updated") for scope in first.scopes
    )
    changed = replace(
        first,
        name="Imported new title",
        start_date=first.start_date + timedelta(days=1),
        end_date=first.end_date + timedelta(days=1),
        scopes=changed_scopes,
        checked_at=later,
    )
    entered, release = Event(), Event()

    def pause(connection, cursor, statement, parameters, context, executemany):
        if context.execution_options.get("planning_graph_snapshot"):
            entered.set()
            assert release.wait(8)

    event.listen(app.extensions["database"], "after_cursor_execute", pause)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(client.get, BASE, base_url=ORIGIN)
            try:
                assert entered.wait(4)
                result = synchronize(
                    database,
                    [source_tests.batch(changed, checked=later, identities=(proof,))],
                    checked_at=later,
                    provider=OFFLINE,
                )
                assert result.status == "success"
            finally:
                release.set()
            response = future.result(timeout=5)
    finally:
        release.set()
        event.remove(app.extensions["database"], "after_cursor_execute", pause)
    old = response.json["items"][0]
    assert old["race"]["name"] == initial["race"]["name"]
    assert old["race"]["start_date"] == initial["race"]["start_date"]
    assert old["scope"]["raw_label"] == initial["scope"]["raw_label"]
    new = client.get(BASE, base_url=ORIGIN).json["items"][0]
    assert (
        new["race"]["id"] == race_id and new["scope_id"] == scope_id and new["id"] == initial["id"]
    )
    assert (
        new["race"]["name"] == changed.name
        and new["race"]["start_date"] == changed.start_date.isoformat()
    )
    assert new["scope"]["raw_label"].endswith(" Updated")


def test_private_planning_contract_matches_scoped_actual_responses(app, database, seeded):
    import json
    from pathlib import Path

    from jsonschema import Draft202012Validator, FormatChecker

    schema = json.loads(
        (Path(__file__).resolve().parents[2] / "contracts/planning.schema.json").read_text(
            encoding="utf-8"
        )
    )
    client, _ = actor_client(app, database)
    changed = save(client, scopes(seeded)[0], "registered")
    listing = client.get(BASE, base_url=ORIGIN)
    missing = write(client, BASE + "/absent", {}, "delete")
    for response, name in [
        (changed, "SavedResult"),
        (listing, "SavedList"),
        (missing, "PlanningError"),
    ]:
        Draft202012Validator(
            {"$defs": schema["$defs"], "$ref": "#/$defs/" + name}, format_checker=FormatChecker()
        ).validate(response.json)


@pytest.mark.parametrize("target", ["x" * 65, "nul\x00id", "surrogate\ud800", {}])
def test_snapshot_rejects_malformed_targets_without_sql_and_session_remains_usable(
    app, database, target
):
    from raceatlas.planning import PlanningNotFound

    _, alice = actor_client(app, database)
    with AccountFlowSession(database) as session:
        actor = session.get(Account, alice)
        queries = []

        def capture(*args):
            queries.append(1)

        event.listen(database, "before_cursor_execute", capture)
        try:
            with pytest.raises(PlanningNotFound):
                snapshot_documents(session, actor, entry_id=target)
            assert queries == []
        finally:
            event.remove(database, "before_cursor_execute", capture)
        assert session.scalar(select(1)) == 1


def test_revoked_second_device_has_passive_401_and_saved_data_remains(app, database, seeded):
    from test_auth_http_sessions import PASSWORD

    client, _ = actor_client(app, database)
    device = app.test_client()
    assert login(device).status_code == 200
    saved = save(client, scopes(seeded)[0], "planned").json["item"]
    assert (
        write(client, "/api/v1/auth/logout-all", {"current_password": PASSWORD}, "post").status_code
        == 204
    )
    denied = device.get(BASE, base_url=ORIGIN)
    assert denied.status_code == 401 and "Set-Cookie" not in denied.headers
    assert login(client).status_code == 200
    assert client.get(BASE, base_url=ORIGIN).json["items"] == [saved]


def test_commit_failure_returns_no_personal_success_and_rolls_back_saved_entry(
    app, database, seeded, monkeypatch
):
    from sqlalchemy.exc import SQLAlchemyError

    import raceatlas.planning_http as http

    client, _ = actor_client(app, database)
    original = http.AccountFlowSession

    class FailedCommit(original):
        def commit(self):
            raise SQLAlchemyError("synthetic private failure")

    monkeypatch.setattr(http, "AccountFlowSession", FailedCommit)
    response = save(client, scopes(seeded)[0])
    assert response.status_code == 503 and "Set-Cookie" not in response.headers
    assert "synthetic private failure" not in response.text
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(SavedEntry)) == 0
    monkeypatch.setattr(http, "AccountFlowSession", original)
    assert client.get(BASE, base_url=ORIGIN).json == {"items": []}


def test_account_lock_closed_before_planning_response_and_exact_text_byte_boundary(
    app, database, seeded, monkeypatch
):
    client, alice = actor_client(app, database)
    target = scopes(seeded)[0]
    scope = seeded.get(EntryScope, target)
    scope.raw_label = "é" * 8192
    seeded.commit()
    assert save(client, target).status_code == 200
    original = app.response_class
    observed = []

    class ObservedResponse(original):
        def __init__(self, response=None, *args, **kwargs):
            if isinstance(response, bytes) and response.startswith(b'{"items":'):
                with Session(database) as observer:
                    assert (
                        observer.scalar(
                            select(Account.id)
                            .where(Account.id == alice)
                            .with_for_update(nowait=True)
                        )
                        == alice
                    )
                observed.append(True)
            super().__init__(response, *args, **kwargs)

    monkeypatch.setattr(app, "response_class", ObservedResponse)
    response = client.get(BASE, base_url=ORIGIN)
    assert response.status_code == 200 and observed == [True]
    assert response.json["items"][0]["scope"]["raw_label"] == "é" * 8192


def test_attested_reorder_replay_refusal_and_absence_never_transfer_private_scope(
    app, database, session
):
    first = source_tests.observation()
    assert (
        synchronize(
            database, [source_tests.batch(first)], checked_at=source_tests.NOW, provider=OFFLINE
        ).status
        == "success"
    )
    race = session.scalar(select(Race))
    proof = source_tests.identities(first, race)
    original_scope_ids = [scope.id for scope in race.scopes]
    client, _ = actor_client(app, database)
    before = [
        save(client, value, status).json["item"]
        for value, status in zip(original_scope_ids, ("planned", "registered"), strict=True)
    ]
    later = source_tests.NOW + timedelta(hours=1)
    reordered = replace(first, scopes=tuple(reversed(first.scopes)), checked_at=later)
    assert (
        synchronize(
            database,
            [source_tests.batch(reordered, checked=later, identities=(proof,))],
            checked_at=later,
            provider=OFFLINE,
        ).status
        == "success"
    )
    assert (
        synchronize(
            database,
            [source_tests.batch(reordered, checked=later)],
            checked_at=later,
            provider=OFFLINE,
        ).status
        == "success"
    )
    failed = synchronize(
        database,
        [source_tests.batch(replace(first, checked_at=later), checked=later)],
        checked_at=later,
        provider=OFFLINE,
    )
    assert failed.status == "failed"
    later += timedelta(hours=1)
    assert (
        synchronize(
            database, [source_tests.batch(checked=later)], checked_at=later, provider=OFFLINE
        ).status
        == "success"
    )
    after = client.get(BASE, base_url=ORIGIN).json["items"]
    expected = {
        item["id"]: (item["scope_id"], item["status"], item["revision"], item["updated_at"])
        for item in before
    }
    assert {
        item["id"]: (item["scope_id"], item["status"], item["revision"], item["updated_at"])
        for item in after
    } == expected
    assert all(
        item["race"]["source_presence"] == "to_verify" and item["race"]["status"] != "cancelled"
        for item in after
    )
