from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
import requests
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from raceatlas import create_app
from raceatlas.auth import authenticate
from raceatlas.auth.admission import AdmissionPolicy, admit_http, key_digest
from raceatlas.auth.csrf import (
    AuthRequestError,
    account_proof,
    issue,
    parse_json,
    valid_cookie,
    verify_request,
)
from raceatlas.auth.errors import InvalidPassword
from raceatlas.auth.http_settings import AuthConfigurationError
from raceatlas.auth.new_passwords import common_passwords, validate_new_password
from raceatlas.auth.passwords import hash_password, verify_password
from raceatlas.models import Account, AuthAdmissionBucket, AuthAdmissionState, PasswordCredential

ORIGIN = "http://127.0.0.1"
CSRF = "synthetic-csrf-key-distinct-000000000"
RATE = "synthetic-rate-key-distinct-111111111"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def isolated(database, monkeypatch):
    with database.begin() as connection:
        connection.execute(delete(AuthAdmissionBucket))
        connection.execute(delete(AuthAdmissionState))

    def forbidden(*args, **kwargs):
        raise AssertionError("Email HTTP forbidden")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)


def configuration(database, **patch):
    return {
        "ENVIRONMENT": "test",
        "DATABASE_URL": database.url,
        "AUTH_ENABLED": True,
        "AUTH_CSRF_KEY": CSRF,
        "AUTH_RATE_KEY": RATE,
        "APP_BASE_URL": ORIGIN,
        "EMAIL_PROVIDER": "development",
        **patch,
    }


@pytest.fixture
def app(database):
    app = create_app(configuration(database))
    yield app
    app.extensions["database"].dispose()


def test_disabled_incomplete_config_preserves_public_health_and_options(database):
    app = create_app(configuration(database, AUTH_ENABLED=False))
    with app.test_client() as client:
        assert client.get("/api/health/live").status_code == 200
        assert client.get("/api/v1/catalog/options").status_code == 200
        assert client.get("/api/v1/auth/csrf").status_code == 503
    assert app.extensions["auth"].state == "disabled"
    app.extensions["database"].dispose()


@pytest.mark.parametrize(
    "patch",
    [
        {"AUTH_CSRF_KEY": ""},
        {"AUTH_RATE_KEY": "short"},
        {"AUTH_RATE_KEY": CSRF},
        {"APP_BASE_URL": "http://external.example.test"},
        {"ENVIRONMENT": "production"},
        {"AUTH_ENABLED": "yes"},
        {"AUTH_CSRF_KEY": "\ud800"},
        {"APP_BASE_URL": "https://user@site.test"},
    ],
)
def test_bad_activation_is_closed_without_secret_or_public_failure(database, patch, caplog):
    app = create_app(configuration(database, **patch))
    with app.test_client() as client:
        response = client.get("/api/v1/auth/csrf")
        assert response.status_code == 503 and "Set-Cookie" not in response.headers
        assert client.get("/api/health/live").status_code == 200
    assert app.extensions["auth"].state == "unavailable"
    assert CSRF not in caplog.text and RATE not in caplog.text
    app.extensions["database"].dispose()


def test_effective_flask_environment_and_overrides_win_over_os(database, monkeypatch):
    monkeypatch.setenv("RACEATLAS_ENV", "production")
    monkeypatch.setenv("AUTH_CSRF_KEY", "wrong-os-key")
    monkeypatch.setenv("APP_BASE_URL", "https://wrong-os.test")
    app = create_app(configuration(database))
    settings = app.extensions["auth"].settings
    assert settings.environment == "test" and settings.origin == ORIGIN and not settings.secure
    assert settings.csrf_key == CSRF.encode()
    assert app.test_client().get("/api/v1/auth/csrf", base_url=ORIGIN).status_code == 200
    app.extensions["database"].dispose()


def test_csrf_cookie_is_host_only_http_only_stable_across_tabs_and_no_store(app):
    client = app.test_client()
    first = client.get("/api/v1/auth/csrf", base_url=ORIGIN)
    cookie = client.get_cookie("raceatlas_csrf_dev", domain="127.0.0.1")
    assert first.status_code == 200 and len(first.json["csrf_token"]) == 64
    assert cookie.http_only and not cookie.secure and cookie.same_site == "Lax"
    assert cookie.domain == "127.0.0.1" and cookie.path == "/"
    assert "Domain=" not in first.headers["Set-Cookie"]
    assert first.headers["Cache-Control"] == "no-store"
    second = client.get("/api/v1/auth/csrf", base_url=ORIGIN)
    assert second.json["csrf_token"] == first.json["csrf_token"]
    assert 0 < second.json["expires_in"] <= first.json["expires_in"]
    assert "Set-Cookie" not in second.headers
    assert all(word not in first.json for word in ["session", "token", "email", "intent"])
    assert CSRF not in str(first.json) and RATE not in str(first.json)


def test_production_secure_cookie_uses_site_host_not_sender(database):
    app = create_app(
        configuration(
            database,
            ENVIRONMENT="production",
            APP_BASE_URL="https://site.example.test",
            EMAIL_PROVIDER="resend",
            RESEND_API_KEY="re_synthetic_never_real",
            EMAIL_FROM="RaceAtlas <sender@mail.example.test>",
            EMAIL_VERIFIED_DOMAIN="mail.example.test",
            EMAIL_SEND_AUTHORIZED="true",
            EMAIL_TRACKING_DISABLED="true",
        )
    )
    client = app.test_client()
    response = client.get("/api/v1/auth/csrf", base_url="https://site.example.test")
    cookie = client.get_cookie("__Host-raceatlas-csrf", domain="site.example.test")
    assert response.status_code == 200 and cookie.secure and cookie.http_only
    assert "Domain=" not in response.headers["Set-Cookie"]
    assert "mail.example.test" not in response.headers["Set-Cookie"]
    app.extensions["database"].dispose()


@pytest.mark.parametrize(
    "origin",
    ["null", "https://evil.test", ORIGIN + ".evil.test", ORIGIN + ":99", ORIGIN + ", " + ORIGIN],
)
def test_csrf_origin_rejects_cross_origin_and_forwarded_spoof(app, origin):
    response = app.test_client().get(
        "/api/v1/auth/csrf",
        base_url=ORIGIN,
        headers={"Origin": origin, "X-Forwarded-Host": "127.0.0.1", "X-Forwarded-Proto": "http"},
    )
    assert response.status_code == 403 and "Set-Cookie" not in response.headers


def test_fetch_metadata_rejects_sibling_and_cross_site_and_query_tokens(app):
    for site in ["cross-site", "same-site"]:
        assert (
            app.test_client()
            .get("/api/v1/auth/csrf", base_url=ORIGIN, headers={"Sec-Fetch-Site": site})
            .status_code
            == 403
        )
    assert app.test_client().get("/api/v1/auth/csrf?token=synthetic").status_code == 400


def test_csrf_binding_mutation_origin_and_server_expiry(app):
    settings = app.extensions["auth"].settings
    token, cookie, _ = issue(settings)

    def check(origin=ORIGIN, proof=token, bearer=None):
        cookie_header = f"{settings.csrf_cookie}={cookie}"
        if bearer is not None:
            cookie_header += f"; {settings.session_cookie}={bearer}"
        headers = {"Cookie": cookie_header, "X-CSRF-Token": proof}
        if origin is not None:
            headers["Origin"] = origin
        with app.test_request_context("/api/v1/auth/login", method="POST", headers=headers):
            from flask import request

            verify_request(settings, request)

    check()
    for args in [{"origin": None}, {"proof": "a" * 64}, {"bearer": "A" * 43}]:
        with pytest.raises(AuthRequestError):
            check(**args)
    auth_token, _, _ = issue(settings, cookie, "A" * 43)
    check(proof=auth_token, bearer="A" * 43)
    with pytest.raises(AuthRequestError):
        check(proof=auth_token)
    _, boundary, _ = issue(settings, now=1000)
    assert valid_cookie(settings, boundary, 2799) and not valid_cookie(settings, boundary, 2800)
    assert not valid_cookie(settings, boundary + "x", 1000)


@pytest.mark.parametrize(
    "body",
    [
        b'{"password":"a","password":"b"}',
        b'{"password":NaN}',
        b'{"password":1}',
        b'{"actor":"x","password":"a"}',
        b"[]",
        b"null",
        b"\xff",
        b'{"token":"A"}',
        b'{"password":' + b"[" * 1200 + b"0" + b"]" * 1200 + b"}",
    ],
)
def test_json_strict_rejects_duplicates_nonstrings_nonfinite_bad_utf8_and_unknown_fields(app, body):
    with app.test_request_context("/", method="POST", data=body, content_type="application/json"):
        from flask import request

        with pytest.raises(AuthRequestError):
            parse_json(request, {"password"})


def test_json_preserves_unicode_spaces_and_nul_and_bounds_body_and_proof(app):
    with app.test_request_context(
        "/", method="POST", json={"password": " Épreuve Exacte\x00 2027 "}
    ):
        from flask import request

        assert parse_json(request, {"password"})["password"] == " Épreuve Exacte\x00 2027 "
    from werkzeug.exceptions import RequestEntityTooLarge

    with app.test_request_context(
        "/", method="POST", data=b" " * 8193, content_type="application/json"
    ):
        from flask import request

        with pytest.raises(RequestEntityTooLarge):
            parse_json(request, {})
    for value in ["A" * 42, "A" * 44, "A" * 42 + "=", None]:
        with app.test_request_context(
            "/", headers={} if value is None else {"X-Account-Proof": value}
        ):
            from flask import request

            with pytest.raises(AuthRequestError):
                account_proof(request)


def test_corpus_pinned_whole_exact_new_secret_only_existing_login_unchanged(session):
    words = common_passwords()
    assert len(words) == 19640 and sum(len(word) >= 15 for word in words) == 48
    word = next(word for word in words if len(word) >= 15 and word != word.upper())
    with pytest.raises(InvalidPassword):
        validate_new_password(word)
    for variant in [word.upper(), " " + word + " ", "Prefix " + word + " Suffix"]:
        validate_new_password(variant)
        assert verify_password(hash_password(variant), variant)
    account = Account(email_normalized="legacy@example.test")
    session.add(account)
    session.flush()
    session.add(
        PasswordCredential(
            account_id=account.id,
            password_hash=hash_password(word),
            email_verified_at=T0,
            session_version=1,
        )
    )
    session.flush()
    assert authenticate(session, "legacy@example.test", word).token


def test_admission_sliding_limits_persist_and_ignore_forwarded_headers(app, database):
    app.extensions["auth"].admission_policy = AdmissionPolicy(per_peer=2)
    client = app.test_client()
    for forwarded in ["198.51.100.1", "198.51.100.2", "198.51.100.3"]:
        response = client.get(
            "/api/v1/auth/csrf",
            base_url=ORIGIN,
            headers={"X-Forwarded-For": forwarded, "Forwarded": f"for={forwarded}"},
        )
    assert response.status_code == 429
    with Session(database) as session:
        peers = session.scalars(
            select(AuthAdmissionBucket).where(AuthAdmissionBucket.namespace == "peer")
        ).all()
        assert len(peers) == 1 and len(peers[0].admissions) == 2
        assert peers[0].key_digest == key_digest(RATE.encode(), "peer", "csrf", "127.0.0.1")
        assert session.get(AuthAdmissionState, 1).denied == 1


def test_admission_is_own_commit_survives_business_rollback_and_does_not_extend_refusal(
    database, monkeypatch
):
    import raceatlas.auth.admission as admission

    now = [T0]
    monkeypatch.setattr(admission, "_now", lambda session: now[0])
    policy = AdmissionPolicy(per_address=2)
    for _ in range(2):
        assert admit_http(
            database,
            RATE.encode(),
            "login",
            "127.0.0.1",
            address="synthetic@example.test",
            policy=policy,
        )
    with Session(database) as business:
        business.add(Account(email_normalized="rolledback@example.test"))
        business.flush()
        business.rollback()
    now[0] += timedelta(seconds=59)
    assert not admit_http(
        database,
        RATE.encode(),
        "login",
        "127.0.0.1",
        address="synthetic@example.test",
        policy=policy,
    )
    with Session(database) as check:
        bucket = check.scalar(
            select(AuthAdmissionBucket).where(AuthAdmissionBucket.namespace == "address")
        )
        assert bucket.expires_at == T0 + timedelta(hours=1) and bucket.admissions == [T0, T0]
    now[0] = T0 + timedelta(seconds=60)
    assert admit_http(
        database,
        RATE.encode(),
        "login",
        "127.0.0.1",
        address="synthetic@example.test",
        policy=policy,
    )


def test_admission_capacity_purge_ttl_and_concurrent_limit(database, monkeypatch):
    import raceatlas.auth.admission as admission

    now = [T0]
    monkeypatch.setattr(admission, "_now", lambda session: now[0])
    policy = AdmissionPolicy(per_global=1, capacity=2)
    barrier = Barrier(2)

    def try_admission():
        barrier.wait(timeout=5)
        return admit_http(database, RATE.encode(), "csrf", "127.0.0.1", policy=policy)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(try_admission) for _ in range(2)]
        assert sorted(f.result(timeout=8) for f in futures) == [False, True]
    with Session(database) as check:
        assert check.scalar(select(func.count()).select_from(AuthAdmissionBucket)) == 2
    now[0] += timedelta(minutes=1)
    assert not admit_http(database, RATE.encode(), "csrf", "192.0.2.1", policy=policy)
    now[0] = T0 + timedelta(hours=1)
    assert admit_http(database, RATE.encode(), "csrf", "192.0.2.1", policy=policy)


def test_auth_concurrency_slots_fail_fast_and_recover(app):
    runtime = app.extensions["auth"]
    with runtime.operation(), runtime.operation():
        with pytest.raises(AuthRequestError) as caught:
            with runtime.operation():
                pytest.fail("slot unexpectedly acquired")
        assert caught.value.status == 429
    with runtime.operation():
        pass


def test_admission_requires_owned_transactional_engine_and_never_takes_external_transaction(
    database,
):
    with database.connect() as connection:
        outer = connection.begin()
        try:
            with pytest.raises(AuthConfigurationError):
                admit_http(connection, RATE.encode(), "csrf", "127.0.0.1")
            assert outer.is_active
        finally:
            outer.rollback()
    with pytest.raises(AuthConfigurationError):
        admit_http(
            database.execution_options(isolation_level="AUTOCOMMIT"),
            RATE.encode(),
            "csrf",
            "127.0.0.1",
        )
    assert not admit_http(database, RATE.encode(), "csrf", True)
    assert not admit_http(database, RATE.encode(), "csrf", "not-an-ip")
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(AuthAdmissionBucket)) == 0


def test_admission_purge_is_indexed_bounded_and_does_not_touch_live_bucket(database, monkeypatch):
    import raceatlas.auth.admission as admission

    monkeypatch.setattr(admission, "_now", lambda session: T0)
    with Session(database) as session, session.begin():
        for i in range(40):
            session.add(
                AuthAdmissionBucket(
                    namespace="peer",
                    key_digest=f"{i:064x}",
                    admissions=[T0 - timedelta(hours=2)],
                    expires_at=T0 - timedelta(hours=1),
                )
            )
        session.add(
            AuthAdmissionBucket(
                namespace="address",
                key_digest="f" * 64,
                admissions=[T0],
                expires_at=T0 + timedelta(hours=1),
            )
        )
    assert admit_http(database, RATE.encode(), "csrf", "127.0.0.1")
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(AuthAdmissionBucket)) == 11
        assert session.get(AuthAdmissionBucket, ("address", "f" * 64)) is not None


def test_auth_openapi_foundation_matches_real_csrf_and_error_responses(app):
    import json
    from pathlib import Path

    from jsonschema import Draft202012Validator, FormatChecker

    spec = json.loads(
        (Path(__file__).resolve().parents[2] / "contracts/auth.openapi.json").read_text(
            encoding="utf-8"
        )
    )
    for schema in spec["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)
    client = app.test_client()
    success = client.get("/api/v1/auth/csrf", base_url=ORIGIN)
    denied = client.get(
        "/api/v1/auth/csrf", base_url=ORIGIN, headers={"Origin": "https://other.test"}
    )
    for response, kind in [(success, "CsrfProof"), (denied, "AccountError")]:
        Draft202012Validator(
            spec["components"]["schemas"][kind], format_checker=FormatChecker()
        ).validate(response.json)
    assert "get" in spec["paths"]["/api/v1/auth/csrf"]


def test_http_admission_does_not_change_public_catalog_epoch(seeded, database):
    from raceatlas.models import CatalogState

    before = seeded.scalar(select(CatalogState.revision))
    assert admit_http(database, RATE.encode(), "csrf", "127.0.0.1")
    assert seeded.scalar(select(CatalogState.revision)) == before


def test_csrf_reused_nonce_reports_remaining_lifetime_without_extending_cookie(app, monkeypatch):
    import raceatlas.auth.http as http

    now = [1000]
    monkeypatch.setattr(http, "wall_time", lambda: now[0])
    client = app.test_client()
    first = client.get("/api/v1/auth/csrf", base_url=ORIGIN)
    now[0] += 10
    second = client.get("/api/v1/auth/csrf", base_url=ORIGIN)
    assert first.json["expires_in"] == 1800 and second.json["expires_in"] == 1790
    assert first.json["csrf_token"] == second.json["csrf_token"]
    assert "Set-Cookie" not in second.headers


def test_fixture_preserves_url_object_and_password_without_rendering_or_connecting():
    from sqlalchemy import create_engine

    engine = create_engine(
        "postgresql+psycopg://synthetic:synthetic_password@127.0.0.1:1/synthetic_test"
    )
    try:
        configured = configuration(engine)
        assert configured["DATABASE_URL"] is engine.url
        assert configured["DATABASE_URL"].password == "synthetic_password"
    finally:
        engine.dispose()


@pytest.mark.parametrize("cached", [False, True])
@pytest.mark.parametrize("size", [8192, 8193, 8222])
def test_json_explicit_byte_boundary_even_after_werkzeug_cache(app, cached, size, monkeypatch):
    import json

    from flask import request
    from werkzeug.exceptions import RequestEntityTooLarge

    import raceatlas.auth.csrf as csrf

    password = " Préserve Exacte\x00 2027 "
    payload = json.dumps({"password": password}, ensure_ascii=False).encode("utf-8")
    payload += b" " * (size - len(payload))
    with app.test_request_context(
        "/", method="POST", data=payload, content_type="application/json"
    ):
        if cached:
            assert len(request.get_data()) == size
        if size > 8192:

            def forbidden(*args, **kwargs):
                pytest.fail("Oversized body reached JSON decoding")

            monkeypatch.setattr(csrf.json, "loads", forbidden)
            with pytest.raises(RequestEntityTooLarge):
                parse_json(request, {"password"})
        else:
            assert parse_json(request, {"password"}) == {"password": password}


def test_uncached_oversize_rejected_without_reading_new_stream(app):
    from io import BytesIO

    from flask import request
    from werkzeug.exceptions import RequestEntityTooLarge

    stream = BytesIO(b"x" * 8222)
    with app.test_request_context(
        "/",
        method="POST",
        content_type="application/json",
        environ_overrides={"wsgi.input": stream, "CONTENT_LENGTH": "8222"},
    ):
        with pytest.raises(RequestEntityTooLarge):
            parse_json(request, {})
        assert stream.tell() == 0
