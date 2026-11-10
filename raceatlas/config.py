import os

from sqlalchemy.engine import make_url


def database_url():
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required; see README.md")
    url = make_url(value)
    if url.drivername != "postgresql+psycopg":
        raise RuntimeError("DATABASE_URL must use postgresql+psycopg")
    return value


def environment():
    value = os.environ.get("RACEATLAS_ENV", "local")
    if value not in {"local", "test", "production"}:
        raise RuntimeError("RACEATLAS_ENV must be local, test or production")
    return value
