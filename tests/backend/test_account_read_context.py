from pathlib import Path

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session
from test_private_planning import ORIGIN, actor_client, save, scopes
from test_private_planning import isolation as isolation

from raceatlas import create_app
from raceatlas.models import PersonalCalendarEventStore


@pytest.fixture
def app(database):
    app = create_app(
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
    yield app
    assert app.extensions["auth"].close(timeout=5)
    app.extensions["database"].dispose()


def token(client):
    return client.get("/api/v1/auth/csrf", base_url=ORIGIN).json["csrf_token"]


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/v1/me", "get"),
        ("/api/v1/me/saved-entries", "get"),
        ("/api/v1/me/calendar.ics", "get"),
        ("/api/v1/me/calendar.ics", "head"),
    ],
)
def test_read_intent_cookie_switch_a_b_a_refused_before_private_sql(
    app, database, seeded, path, method
):
    first, alice = actor_client(app, database)
    second, _ = actor_client(app, database, "bob@example.test")
    target = scopes(seeded)[0]
    save(first, target, "planned")
    save(second, target, "registered")
    proof = token(first)
    assert first.get("/api/v1/me", base_url=ORIGIN).json["account"]["id"] == alice
    settings = app.extensions["auth"].settings
    cookie = first.get_cookie(settings.csrf_cookie, domain="127.0.0.1").value
    # Same nonce isolates the proof's SESSION binding, rather than just different nonces.
    second.set_cookie(settings.csrf_cookie, cookie, domain="127.0.0.1")
    queries = []

    def record(*args):
        queries.append(1)

    engine = app.extensions["database"]
    event.listen(engine, "before_cursor_execute", record)
    try:
        denied = getattr(second, method)(path, base_url=ORIGIN, headers={"X-CSRF-Token": proof})
        assert denied.status_code == 403 and queries == []
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert "Set-Cookie" not in denied.headers
    # Returning to A afterwards does not retroactively validate B's refused read.
    assert (
        getattr(first, method)(path, base_url=ORIGIN, headers={"X-CSRF-Token": proof}).status_code
        == 200
    )
    assert denied.status_code == 403
    assert getattr(second, method)(path, base_url=ORIGIN).status_code == 200


@pytest.mark.parametrize("kind", ["empty", "malformed", "expired", "no_nonce"])
def test_present_invalid_read_proof_never_falls_back_to_compatible_get(
    app, database, seeded, kind, monkeypatch
):
    client, _ = actor_client(app, database)
    proof = token(client)
    if kind == "empty":
        proof = ""
    if kind == "malformed":
        proof = "not-a-mac"
    if kind == "expired":
        from raceatlas.auth import csrf

        now = csrf.time.time()
        monkeypatch.setattr(csrf.time, "time", lambda: now + 1801)
    if kind == "no_nonce":
        client.delete_cookie(app.extensions["auth"].settings.csrf_cookie, domain="127.0.0.1")
    response = client.get(
        "/api/v1/me/calendar.ics", base_url=ORIGIN, headers={"X-CSRF-Token": proof}
    )
    assert response.status_code == 403 and "Set-Cookie" not in response.headers
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(PersonalCalendarEventStore)) == 0


def test_optional_proof_is_not_bearer_and_read_origin_remains_optional_not_permissive(
    app, database, seeded
):
    client, _ = actor_client(app, database)
    proof = token(client)
    path = "/api/v1/me/saved-entries"
    assert client.get(path, base_url=ORIGIN, headers={"X-CSRF-Token": proof}).status_code == 200
    for headers in ({"Origin": "https://wrong.example.test"}, {"Sec-Fetch-Site": "cross-site"}):
        assert (
            client.get(
                path, base_url=ORIGIN, headers={"X-CSRF-Token": proof, **headers}
            ).status_code
            == 403
        )
    settings = app.extensions["auth"].settings
    client.delete_cookie(settings.session_cookie, domain="127.0.0.1")
    anonymous_proof = token(client)
    assert (
        client.get(path, base_url=ORIGIN, headers={"X-CSRF-Token": anonymous_proof}).status_code
        == 401
    )
    # Mutation default still requires Origin even when proof matches cookies.
    assert (
        client.post(
            "/api/v1/auth/login",
            base_url=ORIGIN,
            json={"email": "alice@example.test", "password": "synthetic"},
            headers={"X-CSRF-Token": anonymous_proof},
        ).status_code
        == 403
    )


def test_html_shell_antiframing_and_referrer_headers_are_narrow(app, tmp_path):
    (tmp_path / "index.html").write_text(
        "<!doctype html><title>Synthetic shell</title>", encoding="utf-8"
    )
    app.config["FRONTEND_DIST"] = Path(tmp_path)
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"] == "frame-ancestors 'none'"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" not in app.test_client().get("/api/health/live").headers


def test_preflight_b_a_b_cannot_attest_actor_a_with_proof_bound_to_b(app, database, seeded):
    first, alice = actor_client(app, database)
    second, _ = actor_client(app, database, "bob@example.test")
    proof_b = token(second)  # GETcsrf has captured B before the next tab restores A.
    settings = app.extensions["auth"].settings
    nonce_b = second.get_cookie(settings.csrf_cookie, domain="127.0.0.1").value
    first.set_cookie(settings.csrf_cookie, nonce_b, domain="127.0.0.1")
    me_a = first.get("/api/v1/me", base_url=ORIGIN)
    assert me_a.json["account"]["id"] == alice  # legacy no-header read still compatible
    response = first.get("/api/v1/me", base_url=ORIGIN, headers={"X-CSRF-Token": proof_b})
    assert response.status_code == 403  # cannot combine proofB with identityA as preflight
    assert "Set-Cookie" not in response.headers
    # B's own proof remains valid under B; refusal above must stop UI before this intent.
    assert (
        second.get(
            "/api/v1/me/calendar.ics", base_url=ORIGIN, headers={"X-CSRF-Token": proof_b}
        ).status_code
        == 200
    )
