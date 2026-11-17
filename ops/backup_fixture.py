"""Small explicit synthetic fixture and semantic checks for the local restore CLI."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ops.backup_proof import ROOT, require
from raceatlas import create_app
from raceatlas.auth.passwords import hash_password
from raceatlas.calendar_store import materialize_calendar
from raceatlas.changes import record_change, scope_guards
from raceatlas.models import GeocodeCache, PasswordCredential, Race
from raceatlas.notifications import project_notifications
from raceatlas.notifications_api import mark_all_notifications_read
from raceatlas.planning import create_account, put_saved_entry
from raceatlas.planning_ics import event_uid
from raceatlas.planning_snapshot import PlanningLimits
from raceatlas.seed import seed_synthetic

PASSWORD = " Synthetic backup-only passphrase 2026 "
ONE, TWO = "scope-split-one", "scope-split-two"
ORIGIN = "http://127.0.0.1"


def build_fixture(engine):
    now = datetime(2026, 11, 17, tzinfo=timezone.utc)
    with Session(engine) as session, session.begin():
        seed_synthetic(session)
        alice = create_account(session, "backup-alice@example.test")
        bob = create_account(session, "backup-bob@example.test")
        for actor in (alice, bob):
            session.add(
                PasswordCredential(
                    account_id=actor.id,
                    password_hash=hash_password(PASSWORD),
                    email_verified_at=now,
                    session_version=1,
                )
            )
        # Guard the union once, before any later reentrant saved-scope operations.
        with scope_guards(session, (ONE, TWO)) as guards:
            put_saved_entry(session, alice, ONE, "planned")
            put_saved_entry(session, alice, TWO, "registered")
            put_saved_entry(session, bob, TWO, "interested")
            for index in (1, 2):
                race = session.get(Race, "race-road-split")
                before, after = race.name, f"Synthetic backup change {index}"
                race.name = after
                record_change(
                    session,
                    guards,
                    race_id=race.id,
                    event_key=f"backup-fixture-{index}",
                    kind="business",
                    targets={
                        scope: {"before": {"name": before}, "after": {"name": after}}
                        for scope in (ONE, TWO)
                    },
                    provenance={
                        "source_url": "https://example.test/synthetic-backup",
                        "checked_at": now.isoformat(),
                        "normalization_version": "1.0.0",
                    },
                )
                if index == 1:
                    mark_all_notifications_read(session, alice)
            project_notifications(session, alice)
            project_notifications(session, bob)
        session.add(
            GeocodeCache(
                provider="backup-offline",
                provider_version="1",
                query_key="synthetic-backup-query",
                query={"name": "Commune synthétique"},
                status="positive",
                commune_id="commune-synthetic-a",
                checked_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
        materialize_calendar(session, alice, PlanningLimits())
        return {"alice": alice.id, "bob": bob.id}


def verify_constraints(engine, fixture):
    statements = [
        "INSERT INTO account(id,email_normalized) VALUES (:alice,'duplicate-pk@example.test')",
        "INSERT INTO saved_entry(id,account_id,scope_id,status,revision,"
        "notifications_after_sequence) SELECT 'backup-duplicate',account_id,scope_id,"
        "status,revision,notifications_after_sequence FROM saved_entry "
        "WHERE account_id=:alice LIMIT 1",
        "UPDATE saved_entry SET scope_id='backup-nonexistent-scope' WHERE account_id=:alice",
        "UPDATE saved_entry SET notifications_after_sequence=-1 WHERE account_id=:alice",
        "UPDATE personal_notification SET scope_id='backup-nonexistent-scope' "
        "WHERE account_id=:alice",
        "DELETE FROM entry_scope WHERE id='scope-split-one'",
    ]
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            for statement in statements:
                try:
                    with connection.begin_nested():
                        connection.execute(text(statement), fixture)
                except IntegrityError as error:
                    require(error.orig.sqlstate in {"23505", "23503", "23514"}, "constraint_code")
                else:
                    require(False, "constraint_not_enforced")
            with connection.begin_nested() as nested:
                connection.execute(text("DELETE FROM account WHERE id=:alice"), fixture)
                for table in (
                    "saved_entry",
                    "personal_notification",
                    "personal_calendar_event_store",
                    "password_credential",
                ):
                    require(
                        connection.execute(
                            text(f"SELECT count(*) FROM {table} WHERE account_id=:alice"), fixture
                        ).scalar_one()
                        == 0,
                        "cascade_own",
                    )
                require(
                    connection.execute(
                        text("SELECT count(*) FROM saved_entry WHERE account_id=:bob"), fixture
                    ).scalar_one()
                    == 1,
                    "cascade_other",
                )
                nested.rollback()
        finally:
            transaction.rollback()
    return len(statements) + 1


def verify_http(engine, fixture):
    # No external HTTP, including accidental email-provider use, is allowed.
    with patch("requests.sessions.Session.request", side_effect=RuntimeError("Network forbidden")):
        app = create_app(
            {
                "ENVIRONMENT": "test",
                "DATABASE_URL": engine.url,
                "AUTH_ENABLED": True,
                "APP_BASE_URL": ORIGIN,
                "EMAIL_PROVIDER": "development",
                "AUTH_CSRF_KEY": "synthetic-backup-csrf-key-000000000",
                "AUTH_RATE_KEY": "synthetic-backup-rate-key-111111111",
            }
        )
        checks = 0
        try:
            public = app.test_client()
            selected = json.loads(
                (ROOT / "fixtures/scenarios.v1.json").read_text(encoding="utf-8")
            )["scenarios"][0]["filter"]
            for path in ("/api/v1/races", "/api/v1/map"):
                response = public.get(
                    path, query_string={"filter": json.dumps(selected)}, base_url=ORIGIN
                )
                require(response.status_code == 200 and response.json["total"] > 0, "public_http")
                checks += 1
            require(public.get("/api/v1/me", base_url=ORIGIN).status_code == 401, "anonymous")
            checks += 1
            for label, expected_scopes, unread, item_count in (
                ("alice", {ONE, TWO}, 2, 4),
                ("bob", {TWO}, 2, 2),
            ):
                client = app.test_client()
                csrf = client.get("/api/v1/auth/csrf", base_url=ORIGIN)
                require(csrf.status_code == 200, "csrf")
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": f"backup-{label}@example.test", "password": PASSWORD},
                    headers={"Origin": ORIGIN, "X-CSRF-Token": csrf.json["csrf_token"]},
                    base_url=ORIGIN,
                )
                require(response.status_code == 200, "restored_hash_login")
                actor = client.get("/api/v1/me", base_url=ORIGIN)
                require(actor.status_code == 200, "restored_cookie")
                saved = client.get("/api/v1/me/saved-entries", base_url=ORIGIN)
                require(
                    saved.status_code == 200
                    and {item["scope_id"] for item in saved.json["items"]} == expected_scopes,
                    "restored_planning",
                )
                notifications = client.get("/api/v1/me/notifications", base_url=ORIGIN)
                require(
                    notifications.status_code == 200
                    and notifications.json["unread_count"] == unread
                    and len(notifications.json["items"]) == item_count,
                    "restored_notifications",
                )
                require(
                    {item["scope_id"] for item in notifications.json["items"]} == expected_scopes,
                    "restored_scope_isolation",
                )
                calendar = client.get("/api/v1/me/calendar.ics", base_url=ORIGIN)
                require(
                    calendar.status_code == 200
                    and calendar.headers["Content-Type"].startswith("text/calendar"),
                    "restored_ics",
                )
                require(
                    calendar.data.count(b"BEGIN:VEVENT") == (2 if label == "alice" else 0),
                    "restored_ics_selection",
                )
                if label == "alice":
                    for scope in (ONE, TWO):
                        require(
                            event_uid(fixture[label], scope).encode("ascii") in calendar.data,
                            "restored_uid",
                        )
                checks += 9
            return checks
        finally:
            require(app.extensions["auth"].close(timeout=5), "runtime_close")
            app.extensions["database"].dispose()
