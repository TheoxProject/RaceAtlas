"""Explicit offline inputs; no transport or recurrence is implied by these types."""

from dataclasses import dataclass
from datetime import datetime

from raceatlas.ffc import IdentityAttestation
from raceatlas.ffc.types import CalendarObservation, RaceObservation, SourceKey


@dataclass(frozen=True)
class LocationFact:
    key: SourceKey
    commune_name: str
    department: str
    evidence_id: str
    insee_code: str | None = None


@dataclass(frozen=True)
class AliasProof:
    key: SourceKey
    race_id: str
    expected_key: SourceKey
    expected_revision: int
    evidence_id: str
    decided_at: datetime


@dataclass(frozen=True)
class CompetitionProof:
    key: SourceKey
    competition_id: str | None
    expected_revision: int
    evidence_id: str


@dataclass(frozen=True)
class WindowBatch:
    calendar: CalendarObservation
    details: tuple[RaceObservation, ...]
    locations: tuple[LocationFact, ...] = ()
    aliases: tuple[AliasProof, ...] = ()
    identities: tuple[IdentityAttestation, ...] = ()
    competitions: tuple[CompetitionProof, ...] = ()


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    missing_marked: int
