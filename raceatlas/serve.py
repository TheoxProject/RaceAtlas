"""Prepared private-preview entry point; running it never migrates or seeds a database."""

import base64
import binascii
import os
from dataclasses import dataclass, field
from pathlib import Path
from secrets import compare_digest

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from waitress import serve as run_waitress

from raceatlas import create_app


class HostingConfigError(RuntimeError):
    """A startup error whose message contains variable names, never their secret values."""


@dataclass(frozen=True)
class HostingSettings:
    port: int
    username: str = field(repr=False)
    password: str = field(repr=False)


def load_settings(environ=None):
    values = os.environ if environ is None else environ
    if values.get("RACEATLAS_ENV") != "production":
        raise HostingConfigError("Private preview requires RACEATLAS_ENV=production.")
    try:
        url = make_url(values.get("DATABASE_URL", ""))
        valid_url = (
            url.drivername == "postgresql+psycopg"
            and url.host
            and url.username
            and url.password
            and url.database
        )
    except (ArgumentError, ValueError, TypeError):
        valid_url = False
    if not valid_url:
        raise HostingConfigError("DATABASE_URL requires a complete postgresql+psycopg URL.")
    if url.query.get("sslmode") != "verify-full":
        raise HostingConfigError("DATABASE_URL requires sslmode=verify-full.")
    certificate = url.query.get("sslrootcert")
    try:
        if not isinstance(certificate, str) or not Path(certificate).is_absolute():
            raise ValueError
        with Path(certificate).open("rb") as bundle:
            if not bundle.read(1):
                raise ValueError
    except (OSError, ValueError):
        raise HostingConfigError(
            "sslrootcert must name a readable, nonempty absolute CA file."
        ) from None
    port_text = values.get("PORT", "")
    if (
        not isinstance(port_text, str)
        or not 1 <= len(port_text) <= 5
        or not port_text.isascii()
        or not port_text.isdecimal()
    ):
        raise HostingConfigError("PORT must be an integer from 1 to 65535.")
    port = int(port_text)
    if not 1 <= port <= 65535 or port in {18012, 18013, 19099}:
        raise HostingConfigError("PORT must be a non-reserved integer from 1 to 65535.")
    username = values.get("PREVIEW_USERNAME", "")
    password = values.get("PREVIEW_PASSWORD", "")
    if (
        not isinstance(username, str)
        or not 1 <= len(username) <= 128
        or username != username.strip()
        or ":" in username
        or not username.isprintable()
    ):
        raise HostingConfigError("PREVIEW_USERNAME must contain 1 to 128 printable characters.")
    if (
        not isinstance(password, str)
        or not 32 <= len(password) <= 512
        or password != password.strip()
        or not password.isprintable()
    ):
        raise HostingConfigError("PREVIEW_PASSWORD requires 32 to 512 printable random characters.")
    return HostingSettings(port=port, username=username, password=password)


class PrivatePreview:
    """Mandatory Basic authentication for a preview, distinct from future user accounts."""

    def __init__(self, app, username, password):
        self.app = app
        self._username = username.encode("utf-8")
        self._password = password.encode("utf-8")

    def _authorized(self, header):
        if not isinstance(header, str) or len(header) > 4096:
            return False
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "basic":
            return False
        try:
            decoded = base64.b64decode(parts[1], validate=True)
            decoded.decode("utf-8")
        except (binascii.Error, ValueError, UnicodeDecodeError):
            return False
        username, separator, password = decoded.partition(b":")
        user_matches = compare_digest(username, self._username)
        password_matches = compare_digest(password, self._password)
        return bool(separator) and user_matches and password_matches

    def __call__(self, environ, start_response):
        public_liveness = (
            environ.get("REQUEST_METHOD") in {"GET", "HEAD"}
            and environ.get("PATH_INFO") == "/api/health/live"
            and not environ.get("SCRIPT_NAME")
            and not environ.get("QUERY_STRING")
        )
        if public_liveness or self._authorized(environ.get("HTTP_AUTHORIZATION", "")):

            def private_response(status, headers, exc_info=None):
                headers = [
                    (name, value) for name, value in headers if name.lower() != "cache-control"
                ]
                headers.append(("Cache-Control", "no-store"))
                return start_response(status, headers, exc_info)

            return self.app(environ, private_response)
        body = b"Authentication required."
        start_response(
            "401 Unauthorized",
            [
                ("WWW-Authenticate", 'Basic realm="RaceAtlas private preview", charset="UTF-8"'),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [] if environ.get("REQUEST_METHOD") == "HEAD" else [body]


def create_preview_app():
    settings = load_settings()
    app = create_app()
    app.config["HOSTING_PORT"] = settings.port
    app.wsgi_app = PrivatePreview(app.wsgi_app, settings.username, settings.password)
    return app


def main():
    try:
        app = create_preview_app()
    except HostingConfigError as exc:
        raise SystemExit(str(exc)) from None
    run_waitress(app, host="0.0.0.0", port=app.config["HOSTING_PORT"], threads=4)


if __name__ == "__main__":
    main()
