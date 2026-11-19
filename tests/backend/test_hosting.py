import re
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy.engine import URL, Engine, make_url
from test_catalog import request_page

import raceatlas
from raceatlas import serve


@pytest.fixture()
def hosting_env(tmp_path):
    certificate = tmp_path / "synthetic-ca.pem"
    # Preflight checks readability, not a remote certificate chain or a TLS handshake.
    certificate.write_text("synthetic nonempty CA placeholder", encoding="utf-8")
    url = URL.create(
        "postgresql+psycopg",
        username="synthetic-db-user",
        password="synthetic-db-password",
        host="127.0.0.1",
        port=1,
        database="synthetic-hosting",
        query={"sslmode": "verify-full", "sslrootcert": str(certificate)},
    )
    return {
        "RACEATLAS_ENV": "production",
        "DATABASE_URL": url.render_as_string(hide_password=False),
        "PORT": "10000",
    }


def test_production_preflight_accepts_verified_tls(hosting_env):
    assert serve.load_port(hosting_env) == 10000


@pytest.mark.parametrize(
    "key,value",
    [
        ("RACEATLAS_ENV", None),
        ("RACEATLAS_ENV", "local"),
        ("DATABASE_URL", None),
        ("DATABASE_URL", "malformed-synthetic-secret"),
        ("PORT", None),
        ("PORT", "0"),
        ("PORT", "65536"),
        ("PORT", "18012"),
        ("PORT", "18013"),
        ("PORT", "19099"),
        ("PORT", "10000.5"),
        ("PORT", "9" * 5000),
    ],
    ids=[
        "missing-environment",
        "local-environment",
        "missing-database",
        "malformed-database",
        "missing-port",
        "zero-port",
        "port-too-high",
        "reserved-port-18012",
        "reserved-port-18013",
        "reserved-port-19099",
        "fractional-port",
        "long-port",
    ],
)
def test_invalid_hosting_environment_is_rejected_before_app_factory(
    hosting_env, monkeypatch, key, value
):
    if value is None:
        hosting_env.pop(key)
    else:
        hosting_env[key] = value
    called = []
    original = serve.load_port
    monkeypatch.setattr(serve, "create_app", lambda: called.append(True))
    monkeypatch.setattr(serve, "load_port", lambda: original(hosting_env))
    with pytest.raises(SystemExit) as failure:
        serve.main()
    assert not called
    assert "malformed-synthetic-secret" not in str(failure.value)
    assert hosting_env.get("DATABASE_URL", "not-a-url") not in str(failure.value)


@pytest.mark.parametrize("mode", [None, "", "disable", "prefer", "require", "verify-ca"])
def test_missing_or_weaker_tls_is_rejected(hosting_env, mode):
    url = make_url(hosting_env["DATABASE_URL"])
    query = dict(url.query)
    query.pop("sslmode")
    if mode is not None:
        query["sslmode"] = mode
    hosting_env["DATABASE_URL"] = url.set(query=query).render_as_string(hide_password=False)
    with pytest.raises(serve.HostingConfigError, match="sslmode=verify-full"):
        serve.load_port(hosting_env)


@pytest.mark.parametrize(
    "updates",
    [
        {"drivername": "postgresql"},
        {"username": ""},
        {"password": ""},
        {"database": ""},
    ],
)
def test_incomplete_or_wrong_driver_url_is_rejected(hosting_env, updates):
    url = make_url(hosting_env["DATABASE_URL"]).set(**updates)
    hosting_env["DATABASE_URL"] = url.render_as_string(hide_password=False)
    with pytest.raises(serve.HostingConfigError):
        serve.load_port(hosting_env)


@pytest.mark.parametrize(
    "kind", ["missing", "relative", "absent", "empty", "directory", "duplicate"]
)
def test_explicit_readable_ca_is_required(hosting_env, tmp_path, kind):
    url = make_url(hosting_env["DATABASE_URL"])
    query = dict(url.query)
    if kind == "missing":
        query.pop("sslrootcert")
    elif kind == "relative":
        query["sslrootcert"] = "relative.pem"
    elif kind == "absent":
        query["sslrootcert"] = str(tmp_path / "not-created.pem")
    elif kind == "empty":
        certificate = tmp_path / "empty.pem"
        certificate.touch()
        query["sslrootcert"] = str(certificate)
    elif kind == "directory":
        query["sslrootcert"] = str(tmp_path)
    else:
        query["sslrootcert"] = (query["sslrootcert"], query["sslrootcert"])
    hosting_env["DATABASE_URL"] = url.set(query=query).render_as_string(hide_password=False)
    with pytest.raises(serve.HostingConfigError, match="CA file"):
        serve.load_port(hosting_env)


def test_unreadable_ca_and_duplicate_tls_mode_fail_without_dsn_leak(hosting_env, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("synthetic CA permission failure")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(serve.HostingConfigError, match="CA file") as failure:
        serve.load_port(hosting_env)
    assert hosting_env["DATABASE_URL"] not in str(failure.value)
    url = make_url(hosting_env["DATABASE_URL"])
    query = dict(url.query, sslmode=("verify-full", "disable"))
    hosting_env["DATABASE_URL"] = url.set(query=query).render_as_string(hide_password=False)
    with pytest.raises(serve.HostingConfigError, match="sslmode=verify-full"):
        serve.load_port(hosting_env)


def test_main_starts_public_flask_lazily_without_migrating_or_seeding(
    hosting_env, monkeypatch, capsys, tmp_path
):
    for key, value in hosting_env.items():
        monkeypatch.setenv(key, value)
    (tmp_path / "index.html").write_text("<h1>RaceAtlas</h1>", encoding="utf-8")

    def forbidden(*args, **kwargs):
        raise AssertionError("Startup must not connect, migrate or seed")

    monkeypatch.setattr(Engine, "connect", forbidden)
    monkeypatch.setattr(command, "upgrade", forbidden)
    monkeypatch.setattr(command, "downgrade", forbidden)
    monkeypatch.setattr(raceatlas, "seed_synthetic", forbidden)
    calls = []
    monkeypatch.setattr(serve, "run_waitress", lambda app, **kwargs: calls.append((app, kwargs)))
    serve.main()

    [(app, options)] = calls
    try:
        assert options == {"host": "0.0.0.0", "port": 10000, "threads": 4}
        assert app.config["ENVIRONMENT"] == "production"
        app.config["FRONTEND_DIST"] = tmp_path
        client = app.test_client()
        assert client.get("/api/health/live").json == {"status": "ok"}
        assert client.head("/api/health/live").data == b""
        page = client.get("/")
        assert page.status_code == 200
        assert b"RaceAtlas" in page.data
        assert "WWW-Authenticate" not in page.headers
        assert client.get("/unknown").status_code == 404
    finally:
        assert app.extensions["auth"].close(timeout=5)
        app.extensions["database"].dispose()
    output = capsys.readouterr()
    assert hosting_env["DATABASE_URL"] not in output.out + output.err


def test_public_readiness_failure_hides_connection_details(hosting_env, monkeypatch, caplog):
    for key, value in hosting_env.items():
        monkeypatch.setenv(key, value)
    app = raceatlas.create_app()
    try:
        response = app.test_client().get("/api/health/ready")
        assert response.status_code == 503
        assert response.headers["Cache-Control"] == "no-store"
        public_text = response.get_data(as_text=True) + caplog.text
        assert hosting_env["DATABASE_URL"] not in public_text
        assert "synthetic-db-password" not in public_text
    finally:
        assert app.extensions["auth"].close(timeout=5)
        app.extensions["database"].dispose()


def test_public_launcher_serves_catalog_but_requires_account_session(
    seeded, hosting_env, monkeypatch
):
    origin = "http://127.0.0.1"
    app = raceatlas.create_app(
        {
            "TESTING": True,
            "AUTH_ENABLED": True,
            "APP_BASE_URL": origin,
            "EMAIL_PROVIDER": "development",
            "AUTH_CSRF_KEY": "synthetic-csrf-key-distinct-000000000",
            "AUTH_RATE_KEY": "synthetic-rate-key-distinct-111111111",
        }
    )
    load_production_port = serve.load_port
    monkeypatch.setattr(serve, "load_port", lambda: load_production_port(hosting_env))
    monkeypatch.setattr(serve, "create_app", lambda: app)
    applications = []
    monkeypatch.setattr(
        serve, "run_waitress", lambda application, **_: applications.append(application)
    )
    serve.main()
    [application] = applications
    try:
        client = application.test_client()
        assert client.get("/api/health/ready").json == {"status": "ready"}
        for response in (
            request_page(client),
            request_page(client, map_view=True),
            client.get("/api/v1/catalog/options"),
        ):
            assert response.status_code == 200
            assert "WWW-Authenticate" not in response.headers
        detail = client.get("/api/v1/races/race-gravel")
        assert detail.status_code == 200 and detail.json["id"] == "race-gravel"
        page = client.get("/")
        assert page.status_code == 200
        asset = re.search(r'src="(/assets/[^"]+\.js)"', page.get_data(as_text=True)).group(1)
        compiled = client.get(asset)
        assert compiled.status_code == 200 and len(compiled.data) > 1000
        for path in ("/api/v1/me", "/api/v1/me/saved-entries", "/api/v1/me/notifications"):
            private = client.get(path, base_url=origin)
            assert private.status_code == 401
            assert private.headers["Cache-Control"] == "no-store"
            assert "WWW-Authenticate" not in private.headers
    finally:
        assert app.extensions["auth"].close(timeout=5)
        app.extensions["database"].dispose()
