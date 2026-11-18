import os
from datetime import date, datetime, timezone
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
        connection.execute(
            text(
                "TRUNCATE account, import_run, geocode_cache, competition, "
                "commune, category, race CASCADE"
            )
        )
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
def sport_examples(seeded):
    from raceatlas.models import EntryScope, Race, RaceType, SourceRecord

    day = date(2026, 11, 11)
    examples = (
        ("track", "Épreuve fictive sur piste", "track", []),
        ("hill-climb", "Grimpée fictive", "road", ["hill_climb"]),
    )
    races = []
    for code, name, discipline, types in examples:
        races.append(
            Race(
                id=f"race-{code}",
                name=name,
                discipline=discipline,
                start_date=day,
                end_date=day,
                department="69",
                commune_id="commune-synthetic-a",
                status="scheduled",
                source_presence="present",
                types=[RaceType(code=sport_type) for sport_type in types],
                scopes=[
                    EntryScope(
                        id=f"scope-{code}",
                        position=0,
                        kind="race",
                        identity_status="unverified",
                        eligibility_status="unknown",
                        raw_label="Épreuve synthétique",
                    )
                ],
                source=SourceRecord(
                    provider="synthetic",
                    source_season=2026,
                    race_number=f"SYN-{code}",
                    source_url=f"https://example.test/races/{code}",
                    checked_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
                ),
            )
        )
    seeded.add_all(races)
    seeded.commit()
    try:
        yield
    finally:
        # Remove the two added examples so the next run can test downgrade on this database.
        seeded.rollback()
        for race in races:
            seeded.delete(race)
        seeded.commit()


@pytest.fixture()
def app(database):
    from raceatlas import create_app

    app = create_app({"TESTING": True})
    yield app
    assert app.extensions["auth"].close(timeout=5)
    app.extensions["database"].dispose()
