from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from raceatlas.ffc.types import SourceKey
from raceatlas.models import Commune, GeocodeCache
from raceatlas.sync import LocationFact
from raceatlas.sync.geocoding import CenterCandidate, OfflineProvider, resolve_commune

NOW = datetime(2026, 11, 10, tzinfo=timezone.utc)
FACT = LocationFact(
    SourceKey(2027, "SYNTHETIC001"), "Commune fictive", "26", "source-proof", "26999"
)
CENTER = CenterCandidate("26999", "Commune fictive", "26", 4.9, 45.1)


@pytest.mark.parametrize(
    "candidate",
    [
        replace(CENTER, longitude=float("nan")),
        replace(CENTER, latitude=float("inf")),
        replace(CENTER, longitude=True),
        replace(CENTER, latitude=False),
        replace(CENTER, longitude=181),
        replace(CENTER, latitude=-91),
        replace(CENTER, longitude=45.75, latitude=4.85),
        replace(CENTER, longitude=2.35, latitude=48.85),
        replace(CENTER, longitude=-4, latitude=45),
        replace(CENTER, department="38"),
        replace(CENTER, insee_code="38999"),
        replace(CENTER, precision="race_start"),
        replace(CENTER, provenance="guess"),
        replace(CENTER, insee_code="not-a-code"),
    ],
)
def test_invalid_centers_never_invent_coordinates(session, candidate):
    provider = OfflineProvider("offline", "v1", lambda _: (candidate,))
    result = resolve_commune(session, FACT, provider, NOW)
    assert result.status == "error" and result.commune is None
    assert result.diagnostic == "invalid_commune_center"
    assert session.scalar(select(func.count()).select_from(Commune)) == 0
    assert session.scalar(select(GeocodeCache)).status == "error"


def test_negative_and_error_cache_are_persistent_and_retry_after_bounded_expiry(session):
    calls = []

    def empty(_):
        calls.append(1)
        return ()

    provider = OfflineProvider("offline", "negative-v1", empty)
    first = resolve_commune(session, FACT, provider, NOW)
    session.commit()
    second = resolve_commune(session, FACT, provider, NOW + timedelta(hours=1))
    assert first.status == second.status == "negative"
    assert second.cached and len(calls) == 1
    resolve_commune(session, FACT, provider, NOW + timedelta(days=2))
    assert len(calls) == 2

    def failure(_):
        calls.append(1)
        raise RuntimeError("PRIVATE_RAW_RESPONSE")

    errors = OfflineProvider("offline", "errors-v1", failure)
    result = resolve_commune(session, FACT, errors, NOW)
    cached = resolve_commune(session, FACT, errors, NOW + timedelta(minutes=1))
    assert result.status == "error" and cached.cached and len(calls) == 3
    resolve_commune(session, FACT, errors, NOW + timedelta(minutes=6))
    assert len(calls) == 4
    assert "PRIVATE_RAW_RESPONSE" not in str(session.scalars(select(GeocodeCache.diagnostic)).all())


def test_ambiguous_results_and_conflicting_refreshed_centers_require_review(session):
    ambiguous = OfflineProvider("offline", "ambiguous", lambda _: (CENTER, CENTER))
    assert resolve_commune(session, FACT, ambiguous, NOW).diagnostic == "ambiguous_commune"
    provider = OfflineProvider("offline", "v1", lambda _: (CENTER,))
    first = resolve_commune(session, FACT, provider, NOW)
    changed = OfflineProvider("offline", "v2", lambda _: (replace(CENTER, longitude=5.0),))
    result = resolve_commune(session, FACT, changed, NOW)
    assert result.status == "error" and result.diagnostic == "conflicting_commune_center"
    assert first.commune.longitude == 4.9


def test_provider_version_and_department_separate_homonym_cache_entries(session):
    calls = []
    fact26 = replace(FACT, insee_code=None)
    fact38 = replace(fact26, department="38")

    def lookup(fact):
        calls.append(fact.department)
        return (replace(CENTER, department=fact.department, insee_code=fact.department + "999"),)

    for version, fact in (("v1", fact26), ("v1", fact38), ("v2", fact26)):
        provider = OfflineProvider("offline", version, lookup)
        result = resolve_commune(session, fact, provider, NOW)
        assert result.status == "positive"
        assert result.commune.department == fact.department
    assert calls == ["26", "38", "26"]
    assert session.scalar(select(func.count()).select_from(GeocodeCache)) == 3
    assert session.scalar(select(func.count()).select_from(Commune)) == 2


def test_name_mismatch_without_explicit_insee_is_rejected(session):
    provider = OfflineProvider("offline", "v1", lambda _: (CENTER,))
    result = resolve_commune(
        session, replace(FACT, commune_name="Other place", insee_code=None), provider, NOW
    )
    assert result.status == "error" and result.commune is None


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE geocode_cache SET status='invented'",
        "UPDATE geocode_cache SET status='positive'",
        "UPDATE geocode_cache SET expires_at=checked_at",
        "INSERT INTO geocode_cache SELECT id || '-duplicate', provider,provider_version,query_key,"
        "query,status,commune_id,diagnostic,checked_at,expires_at FROM geocode_cache LIMIT 1",
    ],
)
def test_postgresql_enforces_cache_result_expiry_and_uniqueness(session, statement):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    resolve_commune(session, FACT, OfflineProvider("offline", "v1", lambda _: ()), NOW)
    session.commit()
    with pytest.raises(IntegrityError):
        session.execute(text(statement))
        session.commit()
    session.rollback()
