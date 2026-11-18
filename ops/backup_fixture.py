"""Small explicit synthetic fixture and semantic checks for the local restore CLI."""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ops.backup_common import ROOT, ProofError, guard_path, require
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


def check_probes():
    """Explicit domains/boundaries, not a SQL equivalence parser or permissive regex."""
    result = {}
    enums = [
        ("auth_admission_bucket", "namespace", "namespace", ["global", "peer", "address"]),
        ("auth_challenge", "purpose", "purpose", ["confirmation", "reset"]),
        (
            "commune",
            "department",
            "department",
            ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
        ),
        ("commune", "provenance", "provenance", ["synthetic", "geo_api", "verified_source"]),
        (
            "eligibility_rule",
            "age_reference",
            "age_reference",
            ["season_end", "event_date", "unknown"],
        ),
        ("eligibility_rule", "sex", "sex", ["men", "women", "any", "unknown"]),
        ("email_address_quota", "purpose", "purpose", ["confirmation", "reset"]),
        ("entry_scope", "eligibility", "eligibility_status", ["confirmed", "unknown", "ambiguous"]),
        ("entry_scope", "identity", "identity_status", ["verified", "unverified", "needs_review"]),
        ("entry_scope", "kind", "kind", ["entry_list", "race"]),
        ("geocode_cache", "status", "status", ["positive", "negative", "error"]),
        ("import_item", "status", "status", ["created", "updated", "unchanged", "review", "error"]),
        ("import_run", "status", "status", ["running", "success", "partial", "failed"]),
        ("import_window", "status", "status", ["success", "incomplete", "partial", "failed"]),
        (
            "race",
            "department",
            "department",
            ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
        ),
        ("race", "discipline", "discipline", ["road", "gravel", "mtb", "cyclocross"]),
        ("race", "presence", "source_presence", ["present", "missing", "to_verify"]),
        ("race", "status", "status", ["scheduled", "cancelled", "postponed", "unknown"]),
        ("race_change", "kind", "kind", ["business", "presence"]),
        (
            "race_type",
            "code",
            "code",
            ["road_race", "time_trial", "gravel_race", "xco", "enduro", "downhill", "cyclocross"],
        ),
        ("saved_entry", "status", "status", ["interested", "planned", "registered", "completed"]),
        ("source_record", "provider", "provider", ["synthetic", "ffc"]),
    ]
    for table, suffix, column, values in enums:
        result[(table, f"ck_{table}_{suffix}")] = [({column: value}, True) for value in values] + [
            ({column: "!"}, False)
        ]
    stamp = "2026-11-17T00:00:00Z"
    result[("email_address_quota", "ck_email_address_quota_admitted")] = [
        ({"admitted": n, "admissions": [stamp] * n}, 1 <= n <= 100) for n in (0, 1, 2, 99, 100, 101)
    ] + [({"admitted": 2, "admissions": [stamp]}, False)]
    result[("geocode_cache", "ck_geocode_cache_result")] = [
        (
            {"status": status, "commune_id": commune},
            (status == "positive" and commune is not None)
            or (status in {"negative", "error"} and commune is None),
        )
        for status in ("positive", "negative", "error", "!")
        for commune in (None, "synthetic-commune")
    ]
    allowed = {
        "road": {"road_race", "time_trial"},
        "gravel": {"gravel_race"},
        "mtb": {"xco", "enduro", "downhill"},
        "cyclocross": {"cyclocross"},
    }
    result[("race_type", "ck_race_type_discipline_type")] = [
        ({"discipline": discipline, "code": code}, code in allowed.get(discipline, set()))
        for discipline in (*allowed, "!")
        for code in (
            "road_race",
            "time_trial",
            "gravel_race",
            "xco",
            "enduro",
            "downhill",
            "cyclocross",
            "!",
        )
    ]
    return result


def verify_check_differences(source, restored, source_definitions, restored_definitions):
    old = {(row[0], row[1]): row[2] for row in source_definitions}
    new = {(row[0], row[1]): row[2] for row in restored_definitions}
    require(old.keys() == new.keys(), "constraint_names")
    changed = [key for key in old if old[key] != new[key]]
    probes = check_probes()
    require(all(key in probes for key in changed), "unexpected_constraint_definition")
    checks = 0
    for engine in (source, restored):
        with engine.connect() as connection:
            for table, name in changed:
                expression = connection.exec_driver_sql(
                    "SELECT pg_get_expr(conbin,conrelid) FROM pg_constraint "
                    "WHERE conrelid::regclass::text=%s AND conname=%s AND contype='c'",
                    (table, name),
                ).scalar_one()
                for values, expected in probes[(table, name)]:
                    # All table names are the explicit fixture allowlist above;
                    # expression is this run's trusted catalog, never operator SQL.
                    actual = connection.exec_driver_sql(
                        f"SELECT ({expression}) IS NOT FALSE FROM "
                        f'jsonb_populate_record(NULL::"{table}", %s::jsonb) AS t',
                        (json.dumps(values),),
                    ).scalar_one()
                    require(actual is expected, "check_domain_mismatch")
                    checks += 1
    return dict(
        check_sql_text_match=not changed,
        check_sql_diff_count=len(changed),
        check_domain_assertions=checks,
        check_sql_differences=[
            dict(
                table=key[0],
                name=key[1],
                source_sha256=hashlib.sha256(old[key].encode()).hexdigest(),
                restored_sha256=hashlib.sha256(new[key].encode()).hexdigest(),
            )
            for key in changed
        ],
    )


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
        "UPDATE saved_entry SET scope_id='backup-nonexistent-scope' "
        "WHERE account_id=:alice AND scope_id='scope-split-one'",
        "UPDATE saved_entry SET notifications_after_sequence=-1 WHERE account_id=:alice",
        "UPDATE personal_notification SET scope_id='backup-nonexistent-scope' "
        "WHERE account_id=:alice AND scope_id='scope-split-one' "
        "AND change_id=(SELECT min(change_id) FROM personal_notification WHERE account_id=:alice)",
        "DELETE FROM entry_scope WHERE id='scope-split-one'",
    ]
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            for statement, expected_code in zip(
                statements, ("23505", "23505", "23503", "23514", "23503", "23503"), strict=True
            ):
                try:
                    with connection.begin_nested():
                        connection.execute(text(statement), fixture)
                except IntegrityError as error:
                    require(error.orig.sqlstate == expected_code, "constraint_code")
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


def verify_app_database(app, engine):
    actual = app.extensions["database"]
    require(actual.url == engine.url, "factory_database_url")
    with actual.connect() as connection:
        require(
            connection.exec_driver_sql("SELECT current_database()").scalar_one()
            == engine.url.database,
            "factory_database_identity",
        )


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
            verify_app_database(app, engine)
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


def worker_parameters(environ, fixture):
    from ops.backup_proof import ProofConfig, child_environment, database_url

    require(isinstance(fixture, dict) and set(fixture) == {"alice", "bob"}, "worker_fixture")
    require(
        all(
            isinstance(value, str) and 1 <= len(value) <= 64 and "\0" not in value
            for value in fixture.values()
        ),
        "worker_fixture",
    )
    url = make_url(environ.get("DATABASE_URL", ""))
    match = re.fullmatch("raceatlas_backup_dst_([a-f0-9]{16})", url.database or "")
    require(match is not None, "worker_database")
    nonce = match.group(1)
    output = ROOT / ".local-tools/backup-proof" / nonce
    passfile = output / "empty.pgpass"
    guard_path(passfile, "worker_passfile")
    require(passfile.is_file() and passfile.read_bytes() == b"", "worker_passfile")
    config = ProofConfig(
        Path("."),
        ROOT / ".local-tools/pgdata-lot2-native",
        "raceatlas_backup_src_" + nonce,
        url.database,
        output,
    )
    expected_url = make_url(
        database_url(config, passfile, config.restore_name).render_as_string(hide_password=False)
    )
    # URL parsing omits the empty options query value. The separately checked
    # child libpq environment still fixes PGOPTIONS=""; nonempty options fail.
    require(url == expected_url, "worker_database_url")
    expected = child_environment({}, config, passfile, config.restore_name)
    observed = {key: value for key, value in environ.items() if key.upper().startswith("PG")}
    require(observed == expected, "worker_libpq_environment")
    require(environ.get("RACEATLAS_ENV") == "test", "worker_environment")
    return config, passfile, url


def worker_main():
    from ops.backup_proof import validate_target

    engine = None
    try:
        raw = sys.stdin.buffer.read(4097)
        require(len(raw) <= 4096, "worker_fixture")
        fixture = json.loads(raw.decode("utf-8"))
        config, passfile, url = worker_parameters(os.environ, fixture)
        validate_target(config, passfile, config.restore_name)
        engine = create_engine(url)
        result = dict(result="passed", http_assertions=verify_http(engine, fixture))
    except Exception as error:
        result = dict(
            result="failed",
            code=str(error) if isinstance(error, ProofError) else "operation_failed",
        )
    finally:
        if engine is not None:
            engine.dispose()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(worker_main())
