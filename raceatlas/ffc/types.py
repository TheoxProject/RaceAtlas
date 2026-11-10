"""Immutable observations separate source facts from persistent internal identities."""

from dataclasses import dataclass
from datetime import date, datetime

NORMALIZATION_VERSION = "ffc-observation-1.0.0"
DEPARTMENTS = frozenset("01 03 07 15 26 38 42 43 63 69 73 74".split())


@dataclass(frozen=True)
class Diagnostic:
    code: str
    field: str
    message: str


class AdapterError(ValueError):
    """Safe structured errors: never embeds the input page or participant content."""

    def __init__(self, code, field, message):
        self.diagnostic = Diagnostic(code, field, message)
        super().__init__(f"{code}: {field}: {message}")


@dataclass(frozen=True)
class SourceKey:
    season: int
    race_number: str


@dataclass(frozen=True)
class WindowRequest:
    start: date
    end: date
    department: str


@dataclass(frozen=True)
class CalendarObservation:
    source_url: str
    checked_at: datetime
    requested: WindowRequest
    effective_start: date
    effective_end: date
    effective_department: str | None
    displayed_count: int
    keys: tuple[SourceKey, ...]
    status: str
    diagnostics: tuple[Diagnostic, ...]
    normalization_version: str = NORMALIZATION_VERSION

    def window_document(self):
        return {
            "requested_from": self.requested.start.isoformat(),
            "requested_to": self.requested.end.isoformat(),
            "effective_from": self.effective_start.isoformat(),
            "effective_to": self.effective_end.isoformat(),
            "requested_department": self.requested.department,
            "effective_department": self.effective_department,
            "displayed_count": self.displayed_count,
            "distinct_keys": len(self.keys),
            "status": self.status,
            "reason": "; ".join(item.code for item in self.diagnostics) or None,
        }


@dataclass(frozen=True)
class Restrictions:
    sex: str
    min_age: int | None
    max_age: int | None
    age_reference: str
    age_season: int | None
    engagers: tuple[str, ...]
    other_text: str | None


@dataclass(frozen=True)
class RuleObservation:
    token: str
    category_codes: tuple[str, ...]
    restrictions: Restrictions
    raw_label: str
    evidence_id: str


@dataclass(frozen=True)
class ScopeObservation:
    token: str
    kind: str
    raw_label: str
    eligibility_status: str
    rules: tuple[RuleObservation, ...]
    source_list_id: None = None
    identity_status: str = "unverified"


@dataclass(frozen=True)
class RaceObservation:
    key: SourceKey
    source_url: str
    checked_at: datetime
    name: str
    discipline: str
    types: tuple[str, ...]
    organizer: str | None
    start_date: date
    end_date: date
    department: str
    status: str
    scopes: tuple[ScopeObservation, ...]
    diagnostics: tuple[Diagnostic, ...]
    normalization_version: str = NORMALIZATION_VERSION
