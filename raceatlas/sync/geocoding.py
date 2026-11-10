"""Persistent versioned centre-of-commune cache with an explicitly injected provider."""

import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import timedelta
from itertools import islice
from typing import Callable

from sqlalchemy import select

from raceatlas.ffc.types import DEPARTMENTS, AdapterError
from raceatlas.models import Commune, GeocodeCache

from .fingerprint import fingerprint


@dataclass(frozen=True)
class CenterCandidate:
    insee_code: str
    name: str
    department: str
    longitude: float
    latitude: float
    precision: str = "commune_center"
    provenance: str = "synthetic"


@dataclass(frozen=True)
class OfflineProvider:
    name: str
    version: str
    lookup: Callable


@dataclass(frozen=True)
class Resolution:
    status: str
    commune: Commune | None
    diagnostic: str | None
    cached: bool


def normalized(value):
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _finite(value, minimum, maximum):
    return (
        isinstance(value, (float, int))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and minimum <= value <= maximum
    )


def resolve_commune(session, fact, provider, now):
    """No commit and no networking. Caller owns this transaction and provider permissions."""
    if (
        fact.department not in DEPARTMENTS
        or not isinstance(fact.commune_name, str)
        or not fact.commune_name.strip()
        or not isinstance(fact.evidence_id, str)
        or not fact.evidence_id.strip()
        or fact.insee_code is not None
        and (not isinstance(fact.insee_code, str) or not re.fullmatch(r"[0-9]{5}", fact.insee_code))
    ):
        raise AdapterError("invalid_location_fact", "location", "Explicit commune fact required")
    if now.tzinfo is None:
        raise AdapterError("invalid_timestamp", "geocoding", "Timezone-aware timestamp required")
    if not provider.name.strip() or not provider.version.strip():
        raise AdapterError("invalid_provider", "geocoding", "Named versioned provider required")
    query = {
        "name": normalized(fact.commune_name),
        "department": fact.department,
        "insee_code": fact.insee_code,
    }
    key = fingerprint(query)
    cache = session.scalar(
        select(GeocodeCache).where(
            GeocodeCache.provider == provider.name,
            GeocodeCache.provider_version == provider.version,
            GeocodeCache.query_key == key,
        )
    )
    if cache and cache.expires_at > now:
        return Resolution(
            cache.status,
            session.get(Commune, cache.commune_id) if cache.commune_id else None,
            cache.diagnostic,
            True,
        )
    status, diagnostic, commune = "negative", None, None
    try:
        candidates = tuple(islice(provider.lookup(fact), 2))
    except Exception:
        # Arbitrary provider messages can contain secrets or raw responses; never persist them.
        candidates, status, diagnostic = (), "error", "provider_error"
    if len(candidates) > 1:
        status, diagnostic = "error", "ambiguous_commune"
    elif len(candidates) == 1:
        candidate = candidates[0]
        valid = (
            isinstance(candidate, CenterCandidate)
            and isinstance(candidate.insee_code, str)
            and isinstance(candidate.name, str)
            and re.fullmatch(r"[0-9]{5}", candidate.insee_code)
            and candidate.insee_code[:2] == fact.department
            and candidate.department == fact.department
            and bool(candidate.name.strip())
            and (
                candidate.insee_code == fact.insee_code
                if fact.insee_code
                else normalized(candidate.name) == query["name"]
            )
            and candidate.precision == "commune_center"
            and isinstance(candidate.provenance, str)
            and candidate.provenance in {"synthetic", "geo_api", "verified_source"}
            and _finite(candidate.longitude, -180, 180)
            and _finite(candidate.latitude, -90, 90)
        )
        if not valid:
            status, diagnostic = "error", "invalid_commune_center"
        else:
            commune = session.scalar(
                select(Commune).where(Commune.insee_code == candidate.insee_code)
            )
            if commune and (
                commune.department != candidate.department
                or (commune.longitude, commune.latitude)
                != (candidate.longitude, candidate.latitude)
            ):
                commune, status, diagnostic = None, "error", "conflicting_commune_center"
            else:
                if commune is None:
                    commune = Commune(
                        insee_code=candidate.insee_code,
                        name=candidate.name,
                        department=candidate.department,
                        longitude=candidate.longitude,
                        latitude=candidate.latitude,
                        precision="commune_center",
                        provenance=candidate.provenance,
                        geocoded_at=now,
                    )
                    session.add(commune)
                    session.flush()
                status = "positive"
    ttl = {
        "positive": timedelta(days=7),
        "negative": timedelta(days=1),
        "error": timedelta(minutes=5),
    }
    if cache is None:
        cache = GeocodeCache(
            provider=provider.name, provider_version=provider.version, query_key=key, query=query
        )
        session.add(cache)
    cache.status, cache.diagnostic = status, diagnostic
    cache.commune_id = commune.id if commune else None
    try:
        expires_at = now + ttl[status]
    except OverflowError:
        raise AdapterError(
            "invalid_timestamp", "geocoding", "Cache expiry exceeds date range"
        ) from None
    cache.checked_at, cache.expires_at = now, expires_at
    session.flush()
    return Resolution(status, commune, diagnostic, False)
