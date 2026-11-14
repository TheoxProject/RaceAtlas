from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from threading import Barrier, Event

import pytest
from icalendar import Calendar
from sqlalchemy import delete, event, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from test_auth_http_sessions import PASSWORD, login
from test_private_planning import ORIGIN, actor_client, save, scopes, write
from test_private_planning import isolation as isolation

from raceatlas import create_app
from raceatlas.auth.flows import AccountFlowSession
from raceatlas.models import (
    Account,
    CatalogState,
    EntryScope,
    PersonalCalendarEventStore,
    Race,
    SavedEntry,
)
from raceatlas.planning import put_saved_entry
from raceatlas.planning_snapshot import PlanningLimitError, PlanningLimits

URL = "/api/v1/me/calendar.ics"


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


def get(client, method="get", **headers):
    return getattr(client, method)(URL, base_url=ORIGIN, headers=headers)


def parsed(data):
    return Calendar.from_ical(data).walk("VEVENT")


def rows(database, account_id=None):
    with Session(database) as session:
        stmt = select(PersonalCalendarEventStore)
        if account_id:
            stmt = stmt.where(PersonalCalendarEventStore.account_id == account_id)
        return {
            (r.account_id, r.scope_id): (r.fingerprint, r.stamp, r.sequence)
            for r in session.scalars(stmt)
        }


def test_get_head_private_headers_empty_and_strict_selected_scopes(app, database, seeded):
    assert get(app.test_client()).status_code == 401
    first, alice = actor_client(app, database)
    ids = scopes(seeded)
    assert parsed(get(first).data) == []
    one = save(first, ids[0], "planned").json["item"]
    save(first, ids[1], "completed")
    response = get(first)
    assert response.status_code == 200 and len(parsed(response.data)) == 1
    assert response.headers["Content-Type"] == "text/calendar; charset=utf-8"
    assert (
        response.headers["Content-Disposition"] == 'attachment; filename="raceatlas-planning.ics"'
    )
    assert response.headers["Cache-Control"] == "no-store" and "Set-Cookie" not in response.headers
    first_rows = rows(database)
    assert list(first_rows) == [(alice, one["scope_id"])]
    head = get(first, "head")
    assert (
        head.status_code == 200
        and head.data == b""
        and head.headers["Content-Length"] == str(len(response.data))
    )
    assert rows(database) == first_rows and get(first).data == response.data
    assert get(first, Origin="https://wrong.example.test").status_code == 403
    assert first.get(URL + "?year=2026", base_url=ORIGIN).status_code == 400
    assert get(first, Authorization="Basic cHJldmlldzpwYXNz").status_code == 200
    assert get(app.test_client(), Authorization="Basic cHJldmlldzpwYXNz").status_code == 401


def test_freshness_noop_and_admin_revision_stable_real_content_and_readd_increment(
    app, database, seeded
):
    client, alice = actor_client(app, database)
    target = scopes(seeded)[0]
    saved = save(client, target, "planned").json["item"]
    first = get(client).data
    initial = rows(database)
    with Session(database) as session, session.begin():
        race = session.get(Race, "race-road-split")
        race.source.checked_at += timedelta(days=1)
        race.revision += 1
    assert get(client).data == first and rows(database) == initial
    assert save(client, target, "planned").json["item"]["id"] == saved["id"]
    assert get(client).data == first
    with Session(database) as session, session.begin():
        session.get(Race, "race-road-split").name = "Actually changed"
    changed = parsed(get(client).data)[0]
    assert int(changed["SEQUENCE"]) == 1 and str(changed["UID"]) == str(parsed(first)[0]["UID"])
    assert write(client, "/api/v1/me/saved-entries/" + saved["id"], {}, "delete").status_code == 204
    assert parsed(get(client).data) == [] and len(rows(database, alice)) == 1
    new = save(client, target, "planned").json["item"]
    assert new["id"] != saved["id"]
    again = parsed(get(client).data)[0]
    assert int(again["SEQUENCE"]) == 2 and str(again["UID"]) == str(changed["UID"])
    # Stored stamps represent materialization; sequence remains discriminating even same second.
    assert rows(database)[(alice, target)][2] == 2


@pytest.mark.parametrize(
    "failure", ["response", "text", "events", "cache", "overflow", "dml", "commit"]
)
def test_all_failures_rollback_ledger_and_never_send_partial_calendar(
    app, database, seeded, monkeypatch, failure
):
    import raceatlas.planning_http as http

    client, alice = actor_client(app, database)
    ids = scopes(seeded)
    for target in ids:
        save(client, target, "planned")
    limits = PlanningLimits()
    if failure == "response":
        limits = replace(limits, response_bytes=100)
    if failure == "events":
        limits = replace(limits, events=1)
    if failure == "cache":
        limits = replace(limits, cache_pairs=1)
    if failure == "text":
        with Session(database) as session, session.begin():
            session.get(EntryScope, ids[1]).raw_label = "x" * 16385
    if failure == "overflow":
        assert get(client).status_code == 200
        with Session(database) as session, session.begin():
            row = session.get(PersonalCalendarEventStore, (alice, ids[1]))
            row.sequence = 2147483647
            session.get(Race, "race-road-split").name = "Changed after max"
    before = rows(database)
    if failure == "commit":

        class FailCommit(http.AccountFlowSession):
            def commit(self):
                raise SQLAlchemyError("synthetic commit failure")

        monkeypatch.setattr(http, "AccountFlowSession", FailCommit)

    def broken(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO personal_calendar_event_store"):
            raise SQLAlchemyError("synthetic ledger failure")

    if failure == "dml":
        event.listen(app.extensions["database"], "before_cursor_execute", broken)
    app.extensions["planning_limits"] = limits
    try:
        response = get(client)
    finally:
        if failure == "dml":
            event.remove(app.extensions["database"], "before_cursor_execute", broken)
    assert response.status_code == (503 if failure in ("dml", "commit") else 413)
    assert response.mimetype == "application/json" and "synthetic" not in response.text
    assert rows(database) == before
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(SavedEntry)) == 2


def test_excluded_oversize_scope_does_not_break_export_and_head_materializes(app, database, seeded):
    client, alice = actor_client(app, database)
    ids = scopes(seeded)
    save(client, ids[0], "planned")
    save(client, ids[1], "interested")
    with Session(database) as session, session.begin():
        session.get(EntryScope, ids[1]).raw_label = "x" * 17000
    assert get(client, "head").status_code == 200 and len(rows(database, alice)) == 1
    assert len(parsed(get(client).data)) == 1
    assert client.get("/api/v1/me/saved-entries", base_url=ORIGIN).status_code == 413


def test_batch_201_unique_events_constant_ledger_statements(app, database, seeded):
    client, alice = actor_client(app, database)
    with AccountFlowSession(database) as session, session.begin():
        actor = session.get(Account, alice)
        for index in range(201):
            scope = EntryScope(
                id=f"calendar-scope-{index}",
                race_id="race-road-split",
                position=index,
                kind="race",
                source_list_id=None,
                identity_status="unverified",
                eligibility_status="unknown",
                raw_label=f"scope {index}",
            )
            session.add(scope)
            session.flush()
            put_saved_entry(session, actor, scope.id, "registered")
    statements = []

    def record(connection, cursor, statement, parameters, context, executemany):
        statements.append((statement, context.execution_options))

    event.listen(app.extensions["database"], "before_cursor_execute", record)
    try:
        response = get(client)
    finally:
        event.remove(app.extensions["database"], "before_cursor_execute", record)
    assert response.status_code == 200 and len(parsed(response.data)) == 201
    assert len({str(e["UID"]) for e in parsed(response.data)}) == 201
    assert sum(bool(opts.get("planning_graph_snapshot")) for _, opts in statements) == 1
    assert len([sql for sql, _ in statements if "personal_calendar_event_store" in sql]) == 3
    assert len(rows(database)) == 201


def test_exports_serialized_same_account_without_duplicate_sequence(app, database, seeded):
    first, alice = actor_client(app, database)
    second = app.test_client()
    assert login(second).status_code == 200
    save(first, scopes(seeded)[0], "planned")
    barrier = Barrier(2)

    def export(client):
        barrier.wait(timeout=5)
        return get(client)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(export, [first, second]))
    assert [r.status_code for r in results] == [200, 200]
    assert results[0].data == results[1].data and len(rows(database, alice)) == 1
    assert next(iter(rows(database).values()))[2] == 0


def test_delete_account_cascades_own_cache_preserves_other_and_public_epoch(app, database, seeded):
    first, alice = actor_client(app, database)
    second, bob = actor_client(app, database, "bob@example.test")
    target = scopes(seeded)[0]
    save(first, target, "planned")
    save(second, target, "registered")
    a = get(first).data
    b = get(second).data
    assert str(parsed(a)[0]["UID"]) != str(parsed(b)[0]["UID"])
    with Session(database) as session:
        epoch = session.scalar(select(CatalogState.revision))
    before_other = rows(database, bob)
    assert write(first, "/api/v1/me", {"current_password": PASSWORD}, "delete").status_code == 204
    assert rows(database, alice) == {} and rows(database, bob) == before_other
    assert get(first).status_code == 401 and get(second).data == b
    with Session(database) as session:
        assert session.scalar(select(CatalogState.revision)) == epoch


def test_ledger_scope_cascade_does_not_weaken_saved_fk(app, database, seeded):
    from sqlalchemy.exc import IntegrityError

    client, alice = actor_client(app, database)
    target = scopes(seeded)[0]
    saved = save(client, target, "planned").json["item"]
    get(client)
    with Session(database) as session:
        with pytest.raises(IntegrityError):
            session.execute(delete(EntryScope).where(EntryScope.id == target))
            session.commit()
        session.rollback()
    assert len(rows(database, alice)) == 1
    write(client, "/api/v1/me/saved-entries/" + saved["id"], {}, "delete")
    with Session(database) as session, session.begin():
        session.delete(session.get(EntryScope, target))
    assert rows(database, alice) == {}


def test_renderer_failure_rolls_back_all_new_metadata_and_session_still_usable(
    app, database, seeded, monkeypatch
):
    import raceatlas.calendar_store as store

    client, alice = actor_client(app, database)
    save(client, scopes(seeded)[0], "planned")
    original = store.render_calendar

    def broken(*args):
        raise PlanningLimitError()

    monkeypatch.setattr(store, "render_calendar", broken)
    assert get(client).status_code == 413 and rows(database, alice) == {}
    monkeypatch.setattr(store, "render_calendar", original)
    assert get(client).status_code == 200 and len(rows(database, alice)) == 1


def test_source_snapshot_is_materialized_once_before_ledger_under_concurrent_mutation(
    app, database, seeded
):
    client, alice = actor_client(app, database)
    target = scopes(seeded)[0]
    save(client, target, "planned")
    entered, release = Event(), Event()

    def pause(connection, cursor, statement, parameters, context, executemany):
        if context.execution_options.get("planning_graph_snapshot"):
            entered.set()
            assert release.wait(timeout=8)

    event.listen(app.extensions["database"], "after_cursor_execute", pause)
    try:
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(get, client)
            assert entered.wait(timeout=5)
            with Session(database) as session, session.begin():
                session.get(Race, "race-road-split").name = "Next source title"
                session.get(EntryScope, target).raw_label = "Next source scope"
            release.set()
            old = future.result(timeout=10)
    finally:
        release.set()
        event.remove(app.extensions["database"], "after_cursor_execute", pause)
    assert old.status_code == 200 and "Next source" not in str(parsed(old.data)[0]["SUMMARY"])
    fresh = get(client)
    assert "Next source title" in str(parsed(fresh.data)[0]["SUMMARY"])
    assert "Next source scope" in str(parsed(fresh.data)[0]["SUMMARY"])
    assert int(parsed(fresh.data)[0]["SEQUENCE"]) == 1


def test_account_lock_released_before_calendar_response(app, database, seeded, monkeypatch):
    client, alice = actor_client(app, database)
    save(client, scopes(seeded)[0], "planned")
    original = app.response_class
    observed = []

    class Response(original):
        def __init__(self, response=None, *args, **kwargs):
            if isinstance(response, bytes) and response.startswith(b"BEGIN:VCALENDAR"):
                with Session(database) as session:
                    assert (
                        session.scalar(
                            select(Account.id)
                            .where(Account.id == alice)
                            .with_for_update(nowait=True)
                        )
                        == alice
                    )
                observed.append(True)
            super().__init__(response, *args, **kwargs)

    monkeypatch.setattr(app, "response_class", Response)
    assert get(client).status_code == 200 and observed == [True]


def test_retained_cache_cap_allows_existing_update_but_refuses_new_pair(app, database, seeded):
    client, alice = actor_client(app, database)
    ids = scopes(seeded)
    saved = save(client, ids[0], "planned").json["item"]
    assert get(client).status_code == 200
    app.extensions["planning_limits"] = PlanningLimits(cache_pairs=1)
    with Session(database) as session, session.begin():
        session.get(Race, "race-road-split").name = "Allowed existing change"
    assert get(client).status_code == 200 and next(iter(rows(database).values()))[2] == 1
    assert write(client, "/api/v1/me/saved-entries/" + saved["id"], {}, "delete").status_code == 204
    before = rows(database)
    save(client, ids[1], "planned")
    assert get(client).status_code == 413 and rows(database) == before
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(SavedEntry)) == 1


def test_two_true_changes_same_frozen_database_second_advance_sequence(app, database, seeded):
    client, _ = actor_client(app, database)
    save(client, scopes(seeded)[0], "planned")

    def freeze(connection, cursor, statement, parameters, context, executemany):
        # Synthetic DB-expression clock, isolated to the ledger timestamp SELECT.
        if "clock_timestamp()" in statement and "personal_calendar_event_store" in statement:
            statement = statement.replace(
                "clock_timestamp()", "TIMESTAMPTZ '2026-11-14 08:00:00+00'"
            )
        return statement, parameters

    engine = app.extensions["database"]
    event.listen(engine, "before_cursor_execute", freeze, retval=True)
    try:
        exported = [parsed(get(client).data)[0]]
        for title in ("Second content", "Third content"):
            with Session(database) as session, session.begin():
                session.get(Race, "race-road-split").name = title
            exported.append(parsed(get(client).data)[0])
    finally:
        event.remove(engine, "before_cursor_execute", freeze)
    assert [int(value["SEQUENCE"]) for value in exported] == [0, 1, 2]
    assert len({value["DTSTAMP"].dt for value in exported}) == 1
    assert len({str(value["UID"]) for value in exported}) == 1


def test_positive_exact_ics_byte_boundary_and_composed_description_limit(app, database, seeded):
    client, alice = actor_client(app, database)
    save(client, scopes(seeded)[0], "planned")
    output = get(client).data
    app.extensions["planning_limits"] = PlanningLimits(response_bytes=len(output))
    assert get(client).data == output
    app.extensions["planning_limits"] = PlanningLimits(response_bytes=len(output) - 1)
    assert get(client).status_code == 413
    app.extensions["planning_limits"] = PlanningLimits()
    with Session(database) as session, session.begin():
        race = session.get(Race, "race-road-split")
        # Individually bounded inputs can compose an oversized emitted DESCRIPTION.
        race.source.source_url = "https://example.test/" + "x" * 16000
    before = rows(database, alice)
    assert get(client).status_code == 413 and rows(database, alice) == before


def test_revoked_and_unverified_cookies_cannot_materialize_cache(app, database, seeded):
    first, alice = actor_client(app, database)
    device = app.test_client()
    assert login(device).status_code == 200
    save(first, scopes(seeded)[0], "planned")
    assert (
        write(first, "/api/v1/auth/logout-all", {"current_password": PASSWORD}, "post").status_code
        == 204
    )
    response = get(device)
    assert response.status_code == 401 and "Set-Cookie" not in response.headers
    assert rows(database, alice) == {}
    pending, _ = actor_client(app, database, "pending@example.test", verified=False)
    assert get(pending).status_code == 401
