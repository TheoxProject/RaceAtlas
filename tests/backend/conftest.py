import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def database():
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.fail("TEST_DATABASE_URL is required; use a disposable PostgreSQL database")
    url = make_url(value)
    if url.drivername != "postgresql+psycopg" or not url.database.endswith(("_test", "_review")):
        pytest.fail("Tests require postgresql+psycopg and a database ending _test or _review")
    # The explicit opt-in is required because tests reset their own schema.
    if os.environ.get("RACEATLAS_DISPOSABLE_DB") != "1":
        pytest.fail("Set RACEATLAS_DISPOSABLE_DB=1 for the disposable test database")
    os.environ["DATABASE_URL"] = value
    os.environ["RACEATLAS_ENV"] = "test"
    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    command.check(config)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    command.check(config)
    engine = create_engine(value)
    yield engine
    engine.dispose()


@pytest.fixture()
def session(database):
    with database.begin() as connection:
        connection.execute(text("TRUNCATE competition, commune, category, race CASCADE"))
    with Session(database) as session:
        yield session
        session.rollback()


@pytest.fixture()
def seeded(session):
    from raceatlas.seed import seed_synthetic

    seed_synthetic(session)
    session.commit()
    return session


@pytest.fixture()
def app(database):
    from raceatlas import create_app

    app = create_app({"TESTING": True})
    yield app
    app.extensions["database"].dispose()
