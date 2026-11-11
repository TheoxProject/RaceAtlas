import base64
import re
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy.engine import URL, Engine, make_url
from werkzeug.test import Client
from werkzeug.wrappers import Response

import raceatlas
from raceatlas import serve

USER = "synthetic-preview-user"
PASSWORD = "synthetic-preview-password-" + "x" * 32


def authorization(username=USER, password=PASSWORD):
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": "Basic " + token}


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
        database="synthetic-preview",
        query={"sslmode": "verify-full", "sslrootcert": str(certificate)},
    )
    return {
        "RACEATLAS_ENV": "production",
        "DATABASE_URL": url.render_as_string(hide_password=False),
        "PORT": "10000",
        "PREVIEW_USERNAME": USER,
        "PREVIEW_PASSWORD": PASSWORD,
    }


def test_hosting_settings_hide_secrets_and_only_accept_verified_tls(hosting_env):
    settings = serve.load_settings(hosting_env)
    assert settings.port == 10000
    assert settings.username == USER
    assert settings.password == PASSWORD
    assert USER not in repr(settings) and PASSWORD not in repr(settings)
    assert "DATABASE_URL" not in repr(settings)


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
        ("PREVIEW_USERNAME", None),
        ("PREVIEW_USERNAME", "has:colon"),
        ("PREVIEW_USERNAME", "has\nnewline"),
        ("PREVIEW_USERNAME", "\ud800"),
        ("PREVIEW_PASSWORD", None),
        ("PREVIEW_PASSWORD", "short"),
        ("PREVIEW_PASSWORD", " " * 32),
        ("PREVIEW_PASSWORD", "x" * 513),
        ("PREVIEW_PASSWORD", "x" * 32 + "\ud800"),
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
        "missing-user",
        "user-colon",
        "user-newline",
        "user-surrogate",
        "missing-password",
        "short-password",
        "blank-password",
        "long-password",
        "password-surrogate",
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
    original = serve.load_settings
    monkeypatch.setattr(serve, "create_app", lambda: called.append(True))
    monkeypatch.setattr(serve, "load_settings", lambda: original(hosting_env))
    with pytest.raises(serve.HostingConfigError) as failure:
        serve.create_preview_app()
    assert not called
    assert PASSWORD not in str(failure.value)
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
        serve.load_settings(hosting_env)


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
        serve.load_settings(hosting_env)


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
        serve.load_settings(hosting_env)


def test_unreadable_ca_and_duplicate_tls_mode_fail_without_dsn_leak(hosting_env, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("synthetic CA permission failure")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(serve.HostingConfigError, match="CA file") as failure:
        serve.load_settings(hosting_env)
    assert hosting_env["DATABASE_URL"] not in str(failure.value)
    url = make_url(hosting_env["DATABASE_URL"])
    query = dict(url.query, sslmode=("verify-full", "disable"))
    hosting_env["DATABASE_URL"] = url.set(query=query).render_as_string(hide_password=False)
    with pytest.raises(serve.HostingConfigError, match="sslmode=verify-full"):
        serve.load_settings(hosting_env)


def test_preview_startup_is_lazy_and_never_migrates_or_seeds(hosting_env, monkeypatch, capsys):
    for key, value in hosting_env.items():
        monkeypatch.setenv(key, value)

    def forbidden(*args, **kwargs):
        raise AssertionError("Startup must not connect, migrate or seed")

    monkeypatch.setattr(Engine, "connect", forbidden)
    monkeypatch.setattr(command, "upgrade", forbidden)
    monkeypatch.setattr(command, "downgrade", forbidden)
    monkeypatch.setattr(raceatlas, "seed_synthetic", forbidden)
    application = serve.create_preview_app()
    try:
        assert application.config["ENVIRONMENT"] == "production"
        client = application.test_client()
        assert client.get("/api/health/live").json == {"status": "ok"}
        assert client.head("/api/health/live").data == b""
        assert client.get("/").status_code == 401
        assert client.get("/api/health/ready").status_code == 401
    finally:
        application.extensions["database"].dispose()
    output = capsys.readouterr()
    assert PASSWORD not in output.out + output.err
    assert hosting_env["DATABASE_URL"] not in output.out + output.err


def test_main_uses_only_bounded_waitress_and_reports_generic_startup_errors(
    hosting_env, monkeypatch, capsys
):
    for key, value in hosting_env.items():
        monkeypatch.setenv(key, value)
    calls = []
    monkeypatch.setattr(serve, "run_waitress", lambda app, **kwargs: calls.append((app, kwargs)))
    serve.main()
    try:
        assert len(calls) == 1
        assert calls[0][1] == {"host": "0.0.0.0", "port": 10000, "threads": 4}
        assert isinstance(calls[0][0].wsgi_app, serve.PrivatePreview)
    finally:
        calls[0][0].extensions["database"].dispose()
    monkeypatch.setenv("DATABASE_URL", "malformed-synthetic-secret")
    with pytest.raises(SystemExit) as failure:
        serve.main()
    assert "malformed-synthetic-secret" not in str(failure.value)
    assert PASSWORD not in str(failure.value)
    assert len(calls) == 1
    output = capsys.readouterr()
    assert PASSWORD not in output.out + output.err


@pytest.fixture()
def preview_client():
    def inside(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"private response"]

    return Client(serve.PrivatePreview(inside, USER, PASSWORD), Response)


@pytest.mark.parametrize(
    "path,method",
    [
        ("/", "GET"),
        ("/assets/example.js", "GET"),
        ("/api/v1/races", "GET"),
        ("/api/v1/map", "GET"),
        ("/api/v1/catalog/options", "GET"),
        ("/api/health/ready", "GET"),
        ("/api/health/live/", "GET"),
        ("/api/health/liveness", "GET"),
        ("/api/health/live?probe=extra", "GET"),
        ("/api/health/live", "POST"),
        ("/unknown", "OPTIONS"),
        ("/assets/example.js", "HEAD"),
    ],
)
def test_preview_auth_covers_every_route_and_method_except_exact_liveness(
    preview_client, path, method
):
    response = preview_client.open(path, method=method)
    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert 'charset="UTF-8"' in response.headers["WWW-Authenticate"]
    assert response.data == (b"" if method == "HEAD" else b"Authentication required.")
    allowed = preview_client.open(path, method=method, headers=authorization())
    assert allowed.status_code == 200
    assert allowed.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_only_exact_process_liveness_is_public(preview_client, method):
    assert preview_client.open("/api/health/live", method=method).status_code == 200


@pytest.mark.parametrize(
    "header",
    [
        "",
        "Basic",
        "Bearer synthetic-token",
        "Basic !!!",
        "Basic é",
        "Basic =",
        "Basic YQ== extra",
        "Basic " + base64.b64encode(b"no-colon").decode("ascii"),
        "Basic " + base64.b64encode(b"user:\xff").decode("ascii"),
        "Basic " + "x" * 4097,
        authorization("wrong-user")["Authorization"],
        authorization(password="wrong-password")["Authorization"],
    ],
    ids=[
        "missing",
        "bare-basic",
        "bearer",
        "invalid-alphabet",
        "non-ascii",
        "invalid-padding",
        "multiple-tokens",
        "no-colon",
        "non-utf8",
        "oversized",
        "wrong-user",
        "wrong-password",
    ],
)
def test_bad_basic_headers_are_generic_401_without_reflection(preview_client, header, capsys):
    response = preview_client.get("/assets/private.js", headers={"Authorization": header})
    assert response.status_code == 401
    assert response.data == b"Authentication required."
    output = capsys.readouterr()
    assert PASSWORD not in output.out + output.err
    assert header not in response.get_data(as_text=True) or not header


def test_utf8_credentials_and_password_colons_are_supported():
    def inside(environ, start_response):
        start_response("200 OK", [])
        return [b"ok"]

    client = Client(serve.PrivatePreview(inside, "prévû", PASSWORD + ":é"), Response)
    assert client.get("/", headers=authorization("prévû", PASSWORD + ":é")).status_code == 200
    assert client.get("/", headers=authorization("prévu", PASSWORD + ":é")).status_code == 401


def test_authorized_readiness_failure_never_exposes_database_or_auth_secrets(
    hosting_env, monkeypatch, caplog
):
    for key, value in hosting_env.items():
        monkeypatch.setenv(key, value)
    application = serve.create_preview_app()
    try:
        client = application.test_client()
        response = client.get("/api/health/ready", headers=authorization())
        assert response.status_code == 503
        assert response.headers["Cache-Control"] == "no-store"
        public_text = response.get_data(as_text=True) + caplog.text
        for secret in (
            hosting_env["DATABASE_URL"],
            "synthetic-db-password",
            PASSWORD,
            authorization()["Authorization"],
        ):
            assert secret not in public_text
    finally:
        application.extensions["database"].dispose()


def test_preview_guard_with_real_flask_compiled_assets_and_postgresql(seeded, app):
    app.wsgi_app = serve.PrivatePreview(app.wsgi_app, USER, PASSWORD)
    client = app.test_client()
    assert client.get("/api/health/live").json == {"status": "ok"}
    assert client.get("/api/health/ready").status_code == 401
    assert client.get("/api/v1/races/race-gravel").status_code == 401
    headers = authorization()
    assert client.get("/api/health/ready", headers=headers).json == {"status": "ready"}
    detail = client.get("/api/v1/races/race-gravel", headers=headers)
    assert detail.status_code == 200 and detail.json["id"] == "race-gravel"
    page = client.get("/", headers=headers)
    assert page.status_code == 200
    asset = re.search(r'src="(/assets/[^\"]+\.js)"', page.get_data(as_text=True)).group(1)
    assert client.get(asset).status_code == 401
    compiled = client.get(asset, headers=headers)
    assert compiled.status_code == 200 and len(compiled.data) > 1000
