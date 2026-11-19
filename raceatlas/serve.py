"""Public hosting entry point; running it never migrates or seeds a database."""

import os
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from waitress import serve as run_waitress

from raceatlas import create_app


class HostingConfigError(RuntimeError):
    """A startup error whose message contains variable names, never their secret values."""


def load_port(environ=None):
    values = os.environ if environ is None else environ
    if values.get("RACEATLAS_ENV") != "production":
        raise HostingConfigError("Public hosting requires RACEATLAS_ENV=production.")
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
    return port


def main():
    try:
        port = load_port()
    except HostingConfigError as exc:
        raise SystemExit(str(exc)) from None
    run_waitress(create_app(), host="0.0.0.0", port=port, threads=4)


if __name__ == "__main__":
    main()
