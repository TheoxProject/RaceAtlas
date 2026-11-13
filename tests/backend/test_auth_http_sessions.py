import hashlib
from datetime import datetime, timedelta, timezone

import pytest
import requests
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from raceatlas import create_app
from raceatlas.auth.admission import AdmissionPolicy, key_digest
from raceatlas.auth.new_passwords import common_passwords
from raceatlas.auth.passwords import hash_password
from raceatlas.models import (
    Account,
    AuthAdmissionBucket,
    AuthAdmissionState,
    AuthChallenge,
    AuthSession,
    EmailAddressQuota,
    EmailBudget,
    PasswordCredential,
)

ORIGIN = "http://127.0.0.1"
PASSWORD = " Synthetic Existing Passphrase 2026 "
NEW = " Replacement Exact Passphrase 2027 "
CSRF = "synthetic-csrf-key-distinct-000000000"
RATE = "synthetic-rate-key-distinct-111111111"


@pytest.fixture(autouse=True)
def clean(database, monkeypatch):
    with database.begin() as connection:
        for model in (
            Account,
            EmailAddressQuota,
            EmailBudget,
            AuthAdmissionBucket,
            AuthAdmissionState,
            AuthChallenge,
        ):
            connection.execute(delete(model))

    def forbidden(*args, **kwargs):
        raise AssertionError("Email HTTP forbidden")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)


@pytest.fixture
def app_factory(database):
    apps = []

    def factory(**patch):
        app = create_app(
            {
                "ENVIRONMENT": "test",
                "DATABASE_URL": database.url,
                "AUTH_ENABLED": True,
                "AUTH_CSRF_KEY": CSRF,
                "AUTH_RATE_KEY": RATE,
                "APP_BASE_URL": ORIGIN,
                "EMAIL_PROVIDER": "development",
                **patch,
            }
        )
        apps.append(app)
        return app

    yield factory
    for app in apps:
        assert app.extensions["auth"].close(timeout=5)
        app.extensions["database"].dispose()


@pytest.fixture
def app(app_factory):
    return app_factory()


def identity(database, email="alice@example.test", password=PASSWORD, verified=True):
    with Session(database) as session, session.begin():
        account = Account(email_normalized=email)
        session.add(account)
        session.flush()
        session.add(
            PasswordCredential(
                account_id=account.id,
                password_hash=hash_password(password),
                email_verified_at=datetime(2020, 1, 1, tzinfo=timezone.utc) if verified else None,
                session_version=1,
            )
        )
        return account.id


def origin(client):
    return client.application.extensions["auth"].settings.origin


def bootstrap(client):
    response = client.get("/api/v1/auth/csrf", base_url=origin(client))
    assert response.status_code == 200
    return response.json["csrf_token"]


def send(client, path, body, *, method="post", csrf=None, headers=None):
    proof = bootstrap(client) if csrf is None else csrf
    values = {"Origin": origin(client), "X-CSRF-Token": proof, **(headers or {})}
    return getattr(client, method)(path, json=body, headers=values, base_url=origin(client))


def login(client, email="alice@example.test", password=PASSWORD):
    return send(client, "/api/v1/auth/login", {"email": email, "password": password})


def bearer(client):
    from urllib.parse import urlsplit

    settings = client.application.extensions["auth"].settings
    cookie = client.get_cookie(settings.session_cookie, domain=urlsplit(settings.origin).hostname)
    return cookie.value if cookie is not None else None


def me(client, **kwargs):
    return client.get("/api/v1/me", base_url=origin(client), **kwargs)


def count(database, model):
    with Session(database) as session:
        return session.scalar(select(func.count()).select_from(model))


def test_login_cookie_rotation_two_users_devices_and_basic_header_no_bearer_fallback(app, database):
    alice = identity(database)
    bob = identity(database, "bob@example.test")
    first, second, other = app.test_client(), app.test_client(), app.test_client()
    oldcsrf = bootstrap(first)
    response = send(
        first,
        "/api/v1/auth/login",
        {"email": "alice@example.test", "password": PASSWORD},
        csrf=oldcsrf,
        headers={"Authorization": "Basic c3ludGhldGljOnByZXZpZXc="},
    )
    assert response.status_code == 200 and response.json["account"]["id"] == alice
    assert len(bearer(first)) == 43 and bearer(first) not in response.text
    assert set(response.json) == {"account", "csrf_token", "expires_in"}
    assert (
        response.json["csrf_token"] != oldcsrf and response.headers["Cache-Control"] == "no-store"
    )
    assert login(second).status_code == 200
    assert login(other, "bob@example.test").status_code == 200
    assert bearer(first) != bearer(second)
    assert me(first).json["account"]["id"] == alice and me(other).json["account"]["id"] == bob
    assert me(first, headers={"Authorization": "Basic c3ludGhldGljOnByZXZpZXc="}).status_code == 200
    anonymous = app.test_client()
    assert me(anonymous, headers={"Authorization": f"Bearer {bearer(first)}"}).status_code == 401
    assert send(first, "/api/v1/auth/logout", {}, csrf=oldcsrf).status_code == 403
    assert count(database, AuthSession) == 3


@pytest.mark.parametrize(
    "verified,password,email",
    [
        (False, PASSWORD, "alice@example.test"),
        (True, " Wrong Existing Passphrase ", "alice@example.test"),
        (True, PASSWORD, "unknown@example.test"),
    ],
)
def test_login_failure_is_generic_and_pending_cannot_login(
    app, database, verified, password, email
):
    identity(database, verified=verified)
    client = app.test_client()
    response = login(client, email, password)
    assert response.status_code == 401 and response.json["code"] == "authentication_failed"
    assert bearer(client) is None and count(database, AuthSession) == 0
    assert password not in response.text and email not in response.text


def test_login_existing_common_password_is_not_new_password_policy(app, database):
    word = next(word for word in common_passwords() if len(word) >= 15)
    identity(database, password=word)
    assert login(app.test_client(), password=word).status_code == 200


@pytest.mark.parametrize(
    "path,method,body",
    [
        ("/api/v1/auth/logout-all", "post", {"current_password": " Wrong Current Passphrase "}),
        (
            "/api/v1/auth/password/change",
            "post",
            {"current_password": " Wrong Current Passphrase ", "new_password": NEW},
        ),
        ("/api/v1/me", "delete", {"current_password": " Wrong Current Passphrase "}),
    ],
)
def test_wrong_current_password_403_keeps_cookie_sessions_and_other_device(
    app, database, path, method, body
):
    identity(database)
    first, second = app.test_client(), app.test_client()
    assert login(first).status_code == login(second).status_code == 200
    before = bearer(first)
    response = send(first, path, body, method=method)
    assert response.status_code == 403 and response.json["code"] == "reauthentication_failed"
    assert "Set-Cookie" not in response.headers and bearer(first) == before
    assert me(first).status_code == me(second).status_code == 200
    assert count(database, AuthSession) == 2 and count(database, Account) == 1


def test_logout_current_leaves_other_device_and_no_password_required(app, database):
    identity(database)
    first, second = app.test_client(), app.test_client()
    assert login(first).status_code == login(second).status_code == 200
    response = send(first, "/api/v1/auth/logout", {})
    assert (
        response.status_code == 204
        and not response.data
        and response.headers["Cache-Control"] == "no-store"
    )
    assert bearer(first) is None and me(second).status_code == 200
    assert count(database, AuthSession) == 1


@pytest.mark.parametrize("operation", ["logout-all", "change"])
def test_sensitive_success_revokes_all_devices_without_auto_login(app, database, operation):
    identity(database)
    first, second = app.test_client(), app.test_client()
    assert login(first).status_code == login(second).status_code == 200
    path = (
        "/api/v1/auth/logout-all" if operation == "logout-all" else "/api/v1/auth/password/change"
    )
    body = {"current_password": PASSWORD}
    if operation == "change":
        body["new_password"] = NEW
    response = send(first, path, body)
    assert (
        response.status_code == 204 and bearer(first) is None and count(database, AuthSession) == 0
    )
    assert me(second).status_code == 401 and bearer(second) is not None
    assert login(second, password=NEW if operation == "change" else PASSWORD).status_code == 200


@pytest.mark.parametrize("kind", ["malformed", "expired", "revoked"])
def test_invalid_cookie_401_is_passive_then_csrf_login_replaces_it(app, database, kind):
    identity(database)
    client = app.test_client()
    if kind == "malformed":
        client.set_cookie("raceatlas_session_dev", "malformed", domain="127.0.0.1")
    else:
        assert login(client).status_code == 200
        digest = hashlib.sha256(bearer(client).encode()).hexdigest()
        with Session(database) as session, session.begin():
            row = session.get(AuthSession, digest)
            if kind == "revoked":
                session.delete(row)
            else:
                row.created_at = datetime.now(timezone.utc) - timedelta(days=8)
                row.last_seen_at = row.created_at
                row.expires_at = row.created_at + timedelta(days=7)
    before = bearer(client)
    response = me(client)
    assert response.status_code == 401 and bearer(client) == before
    assert "Set-Cookie" not in response.headers
    assert login(client).status_code == 200


def test_login_can_replace_stale_cookie_directly_and_failed_login_keeps_valid_session(
    app, database
):
    identity(database)
    client = app.test_client()
    client.set_cookie("raceatlas_session_dev", "malformed", domain="127.0.0.1")
    assert login(client).status_code == 200
    token = bearer(client)
    response = login(client, password=" Wrong Current Passphrase ")
    assert response.status_code == 401 and bearer(client) == token
    assert me(client).status_code == 200


def test_common_new_password_rejected_without_revocation_or_cookie_change(app, database):
    identity(database)
    client = app.test_client()
    assert login(client).status_code == 200
    before = bearer(client)
    word = next(word for word in common_passwords() if len(word) >= 15)
    response = send(
        client, "/api/v1/auth/password/change", {"current_password": PASSWORD, "new_password": word}
    )
    assert response.status_code == 400 and response.json["code"] == "invalid_password"
    assert bearer(client) == before and me(client).status_code == 200
    assert count(database, AuthSession) == 1


def test_invalid_session_is_401_before_classifying_wrong_current_password(app, database):
    client = app.test_client()
    response = send(
        client,
        "/api/v1/auth/password/change",
        {"current_password": " Wrong Current Passphrase ", "new_password": NEW},
    )
    assert response.status_code == 401


def test_csrf_origin_json_and_admission_enforced_before_kdf(app, database, monkeypatch):
    import raceatlas.auth.sessions_http as http

    calls = []
    original = http.auth.authenticate

    def verify(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(http.auth, "authenticate", verify)
    identity(database)
    client = app.test_client()
    csrf = bootstrap(client)
    for headers in [{"Origin": "null"}, {"Origin": "http://evil.test"}, {"X-CSRF-Token": "0" * 64}]:
        assert (
            send(
                client,
                "/api/v1/auth/login",
                {"email": "alice@example.test", "password": PASSWORD},
                csrf=csrf,
                headers=headers,
            ).status_code
            == 403
        )
    assert (
        send(
            client,
            "/api/v1/auth/login",
            {"email": "alice@example.test", "password": PASSWORD, "actor": "other"},
            csrf=csrf,
        ).status_code
        == 400
    )
    assert calls == []
    app.extensions["auth"].admission_policy = AdmissionPolicy(per_address=1)
    assert login(client, password=" Wrong Current Passphrase ").status_code == 401
    assert login(client).status_code == 429 and calls == [1]


def test_cached_oversize_real_login_rejected_before_kdf(app, monkeypatch):
    from flask import request

    import raceatlas.auth.sessions_http as http

    @app.before_request
    def cache_body():
        if request.path == "/api/v1/auth/login":
            request.get_data()

    def forbidden(*args, **kwargs):
        pytest.fail("KDF reached for oversized body")

    monkeypatch.setattr(http.auth, "authenticate", forbidden)
    client = app.test_client()
    csrf = bootstrap(client)
    response = client.post(
        "/api/v1/auth/login",
        base_url=ORIGIN,
        content_type="application/json",
        data=b'{"email":"alice@example.test","password":"synthetic"}' + b" " * 8192,
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
    )
    assert response.status_code == 413


@pytest.mark.parametrize("operation", ["login", "change"])
def test_commit_failure_publishes_no_cookie_and_rolls_back_private_state(
    app, database, monkeypatch, operation
):
    import raceatlas.auth.sessions_http as http

    identity(database)
    client = app.test_client()
    if operation == "change":
        assert login(client).status_code == 200
    csrf = bootstrap(client)
    before = bearer(client)
    original = http.AccountFlowSession

    class BrokenCommit(original):
        def commit(self):
            raise SQLAlchemyError("synthetic private secret must not escape")

    monkeypatch.setattr(http, "AccountFlowSession", BrokenCommit)
    path = "/api/v1/auth/login" if operation == "login" else "/api/v1/auth/password/change"
    body = (
        {"email": "alice@example.test", "password": PASSWORD}
        if operation == "login"
        else {"current_password": PASSWORD, "new_password": NEW}
    )
    response = send(client, path, body, csrf=csrf)
    assert response.status_code == 503 and "Set-Cookie" not in response.headers
    assert bearer(client) == before and "synthetic private secret" not in response.text
    assert count(database, AuthSession) == (0 if operation == "login" else 1)
    monkeypatch.setattr(http, "AccountFlowSession", original)
    assert login(app.test_client()).status_code == 200


def test_production_cookies_are_secure_host_only_and_no_email_domain(app_factory, database):
    identity(database)
    app = app_factory(
        ENVIRONMENT="production",
        APP_BASE_URL="https://site.example.test",
        EMAIL_PROVIDER="resend",
        RESEND_API_KEY="re_synthetic_never_real",
        EMAIL_FROM="RaceAtlas <sender@mail.example.test>",
        EMAIL_VERIFIED_DOMAIN="mail.example.test",
        EMAIL_SEND_AUTHORIZED="true",
        EMAIL_TRACKING_DISABLED="true",
    )
    client = app.test_client()
    response = login(client)
    cookie = client.get_cookie("__Host-raceatlas-session", domain="site.example.test")
    assert (
        response.status_code == 200
        and cookie.secure
        and cookie.http_only
        and cookie.same_site == "Lax"
    )
    assert cookie.path == "/" and "Domain=" not in str(response.headers.getlist("Set-Cookie"))
    assert "mail.example.test" not in str(response.headers.getlist("Set-Cookie"))
    assert send(client, "/api/v1/auth/logout", {}).status_code == 204
    assert bearer(client) is None


def test_delete_purges_only_own_private_data_and_b2_quotas_keeps_budgets_and_epoch(
    app, database, seeded
):
    import hmac

    from raceatlas.models import CatalogState, Race, SavedEntry
    from raceatlas.planning import put_saved_entry

    alice = identity(database)
    bob = identity(database, "bob@example.test")
    scope = seeded.get(Race, "race-road-combined").scopes[0]
    for account_id in [alice, bob]:
        put_saved_entry(seeded, seeded.get(Account, account_id), scope.id, "planned")
    seeded.commit()
    baseline = seeded.scalar(select(CatalogState.revision))
    now = datetime.now(timezone.utc)
    with Session(database) as setup, setup.begin():
        setup.add(
            EmailBudget(
                id=1, day=now.date(), month=now.date().replace(day=1), day_count=7, month_count=17
            )
        )
        for account_id, email, digest in [
            (alice, "alice@example.test", "a" * 64),
            (bob, "bob@example.test", "b" * 64),
        ]:
            setup.add(
                AuthChallenge(
                    account_id=account_id,
                    purpose="reset",
                    token_digest=digest,
                    credential_version=1,
                    created_at=now,
                    expires_at=now + timedelta(minutes=30),
                )
            )
            setup.add(
                EmailAddressQuota(
                    address_digest=hmac.new(
                        RATE.encode(), email.encode(), hashlib.sha256
                    ).hexdigest(),
                    purpose="reset",
                    admissions=[now],
                    admitted=1,
                    window_started_at=now,
                    last_admitted_at=now,
                    expires_at=now + timedelta(hours=2),
                )
            )
    first, second, other = app.test_client(), app.test_client(), app.test_client()
    assert login(first).status_code == login(second).status_code == 200
    assert login(other, "bob@example.test").status_code == 200
    response = send(first, "/api/v1/me", {"current_password": PASSWORD}, method="delete")
    assert response.status_code == 204 and bearer(first) is None
    assert (
        count(database, Account)
        == count(database, PasswordCredential)
        == count(database, AuthSession)
        == 1
    )
    assert (
        count(database, AuthChallenge)
        == count(database, SavedEntry)
        == count(database, EmailAddressQuota)
        == 1
    )
    assert me(other).json["account"]["id"] == bob and me(second).status_code == 401
    with Session(database) as check:
        assert check.scalar(select(Account.id)) == bob
        assert (
            check.get(EmailBudget, 1).day_count == 7 and check.get(EmailBudget, 1).month_count == 17
        )
        digest = key_digest(RATE.encode(), "address", "login", "alice@example.test")
        assert check.get(AuthAdmissionBucket, ("address", digest)) is not None
        assert check.scalar(select(CatalogState.revision)) == baseline
    assert first.get("/api/v1/catalog/options", base_url=ORIGIN).status_code == 200


def test_no_actor_override_and_disabled_accounts_preserve_public(app, app_factory, database):
    alice = identity(database)
    bob = identity(database, "bob@example.test")
    client = app.test_client()
    assert login(client).status_code == 200
    assert (
        send(
            client, "/api/v1/me", {"current_password": PASSWORD, "actor_id": bob}, method="delete"
        ).status_code
        == 400
    )
    assert client.get("/api/v1/me?user_id=" + bob, base_url=ORIGIN).status_code == 400
    assert me(client).json["account"]["id"] == alice and count(database, Account) == 2
    disabled = app_factory(AUTH_ENABLED=False).test_client()
    assert disabled.get("/api/v1/me").status_code == 503
    assert (
        disabled.post("/api/v1/auth/login", json={"email": "x", "password": "x"}).status_code == 503
    )
    assert disabled.get("/api/health/live").status_code == 200


def test_session_and_locks_closed_before_cookie_publication_and_get_does_not_extend_expiry(
    app, database, monkeypatch
):
    from http.cookies import SimpleCookie

    from raceatlas.models import Account

    alice = identity(database)
    client = app.test_client()
    csrf = bootstrap(client)
    original = app.response_class.set_cookie
    observed = []

    def publish(response, key, *args, **kwargs):
        if key == app.extensions["auth"].settings.session_cookie:
            with Session(database) as observer:
                assert (
                    observer.scalar(
                        select(Account.id).where(Account.id == alice).with_for_update(nowait=True)
                    )
                    == alice
                )
            observed.append(True)
        return original(response, key, *args, **kwargs)

    monkeypatch.setattr(app.response_class, "set_cookie", publish)
    response = send(
        client,
        "/api/v1/auth/login",
        {"email": "alice@example.test", "password": PASSWORD},
        csrf=csrf,
    )
    assert response.status_code == 200 and observed == [True]
    cookies = SimpleCookie()
    for value in response.headers.getlist("Set-Cookie"):
        cookies.load(value)
    assert 0 < int(cookies["raceatlas_session_dev"]["max-age"]) <= 604800
    cookie = client.get_cookie("raceatlas_session_dev", domain="127.0.0.1")
    expiry = cookie.expires
    current = me(client)
    assert current.status_code == 200 and "Set-Cookie" not in current.headers
    assert client.get_cookie("raceatlas_session_dev", domain="127.0.0.1").expires == expiry


def test_real_http_change_blocks_then_revokes_other_device_under_account_lock(
    app, database, monkeypatch
):
    import time
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue
    from threading import Event, current_thread

    from sqlalchemy import event, text

    import raceatlas.auth as auth
    from raceatlas.auth.flows import AccountFlowSession

    identity(database)
    first, second = app.test_client(), app.test_client()
    assert login(first).status_code == login(second).status_code == 200
    proof = bootstrap(first)
    entered, release = Event(), Event()
    pids = Queue()
    original = auth.verify_password

    def verify(*args, **kwargs):
        result = original(*args, **kwargs)
        if current_thread().name == "http-change":
            assert result
            entered.set()
            assert release.wait(5)
        return result

    def began(session, transaction, connection):
        if current_thread().name == "http-reader":
            pids.put(connection.scalar(select(func.pg_backend_pid())))

    monkeypatch.setattr(auth, "verify_password", verify)
    event.listen(AccountFlowSession, "after_begin", began)

    def change():
        current_thread().name = "http-change"
        return send(
            first,
            "/api/v1/auth/password/change",
            {"current_password": PASSWORD, "new_password": NEW},
            csrf=proof,
        )

    def read():
        current_thread().name = "http-reader"
        return me(second)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(change)
            try:
                assert entered.wait(4)
                b = pool.submit(read)
                pid = pids.get(timeout=3)
                blocked = False
                deadline = time.monotonic() + 0.8
                with database.connect() as observer:
                    while time.monotonic() < deadline:
                        if (
                            observer.scalar(
                                text("SELECT cardinality(pg_blocking_pids(:pid))"), {"pid": pid}
                            )
                            > 0
                        ):
                            blocked = True
                            break
                        time.sleep(0.005)
                assert blocked, "Reader did not wait for real Account lock"
            finally:
                release.set()
            assert a.result(timeout=5).status_code == 204
            assert b.result(timeout=5).status_code in {401, 503}
        assert me(second).status_code == 401
    finally:
        release.set()
        event.remove(AccountFlowSession, "after_begin", began)


def test_delayed_passive_401_cannot_overwrite_fresh_login_from_another_tab(
    app, database, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, current_thread

    import raceatlas.auth as auth
    from raceatlas.auth.errors import AuthenticationFailed

    identity(database)
    bob = identity(database, "bob@example.test")
    browser = app.test_client()
    assert login(browser).status_code == 200
    old = bearer(browser)
    old_request = app.test_client()
    old_request.set_cookie("raceatlas_session_dev", old, domain="127.0.0.1")
    with Session(database) as session, session.begin():
        session.execute(
            delete(AuthSession).where(
                AuthSession.token_digest == hashlib.sha256(old.encode()).hexdigest()
            )
        )
    entered, release = Event(), Event()
    original = auth.resolve_session

    def resolve(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except AuthenticationFailed:
            if current_thread().name == "old-passive-request":
                entered.set()
                assert release.wait(5)
            raise

    monkeypatch.setattr(auth, "resolve_session", resolve)

    def delayed():
        current_thread().name = "old-passive-request"
        return me(old_request)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(delayed)
        try:
            assert entered.wait(3)
            assert login(browser, "bob@example.test").status_code == 200
            fresh = bearer(browser)
            assert fresh != old and me(browser).json["account"]["id"] == bob
        finally:
            release.set()
        late = future.result(timeout=5)
    assert late.status_code == 401 and "Set-Cookie" not in late.headers
    assert bearer(browser) == fresh and me(browser).json["account"]["id"] == bob


def test_auth_contract_matches_session_success_and_reauthentication_errors(app, database):
    import json
    from pathlib import Path

    from jsonschema import Draft202012Validator, FormatChecker

    spec = json.loads(
        (Path(__file__).resolve().parents[2] / "contracts/auth.openapi.json").read_text(
            encoding="utf-8"
        )
    )
    identity(database)
    client = app.test_client()
    logged = login(client)
    current = me(client)
    forbidden = send(
        client, "/api/v1/auth/logout-all", {"current_password": " Wrong Current Passphrase "}
    )
    unauth = me(app.test_client())
    for response, name in [
        (logged, "LoginSuccess"),
        (current, "CurrentAccount"),
        (forbidden, "AccountError"),
        (unauth, "AccountError"),
    ]:
        schema = {"components": spec["components"], "$ref": "#/components/schemas/" + name}
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(response.json)
    assert "Set-Cookie" not in unauth.headers and "Set-Cookie" not in forbidden.headers


def test_new_password_http_preserves_unicode_nul_and_spaces_exactly(app, database):
    identity(database)
    client = app.test_client()
    assert login(client).status_code == 200
    new = " Nouvelle Épreuve\x00 2027  "
    assert (
        send(
            client,
            "/api/v1/auth/password/change",
            {"current_password": PASSWORD, "new_password": new},
        ).status_code
        == 204
    )
    assert login(client, password=new).status_code == 200
    token = bearer(client)
    assert login(client, password=new.strip()).status_code == 401
    assert bearer(client) == token and me(client).status_code == 200
