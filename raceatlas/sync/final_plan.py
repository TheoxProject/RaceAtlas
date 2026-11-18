"""Pure, detached finalization decisions. No ORM, Session, SQL or I/O."""

import json
from dataclasses import dataclass, replace
from datetime import date, datetime

COVERAGE_UNVERIFIED = "coverage_unverified"
BUSINESS_KEYS = (
    "name",
    "discipline",
    "types",
    "organizer",
    "start_date",
    "end_date",
    "department",
    "status",
    "scopes",
)


@dataclass(frozen=True)
class WindowState:
    id: str
    status: str
    diagnostics: tuple[str, ...]
    requested_from: date
    requested_to: date
    effective_from: date
    effective_to: date
    requested_department: str
    effective_department: str | None
    displayed_count: int
    distinct_keys: int
    source_url: str
    checked_at: datetime


@dataclass(frozen=True)
class ItemState:
    id: str
    window_id: str
    race_id: str | None
    status: str
    diagnostic: str | None
    observed: bytes | None


@dataclass(frozen=True)
class RaceState:
    id: str
    revision: int
    department: str
    start_date: date
    end_date: date
    presence: str
    checked_at: datetime
    presence_checked_at: datetime | None
    scope_ids: tuple[str, ...]
    history_facts: bytes

    @property
    def baseline(self):
        return max(self.checked_at, self.presence_checked_at or self.checked_at)


@dataclass(frozen=True)
class FinalInputs:
    run_id: str
    version: str
    supported_version: str
    now: datetime
    accepted: tuple[str, ...]
    windows: tuple[WindowState, ...]
    items: tuple[ItemState, ...]
    races: tuple[RaceState, ...]


@dataclass(frozen=True)
class PresenceStamp:
    race_id: str
    at: datetime


@dataclass(frozen=True)
class AbsenceTransition:
    race_id: str
    before: str
    scope_ids: tuple[str, ...]
    witness_window_id: str
    source_url: str
    checked_at: datetime
    version: str


@dataclass(frozen=True)
class FinalizationPlan:
    items: tuple[ItemState, ...]
    windows: tuple[WindowState, ...]
    stamps: tuple[PresenceStamp, ...]
    transitions: tuple[AbsenceTransition, ...]
    scope_ids: tuple[str, ...]
    affected_windows: tuple[str, ...]
    run_status: str
    missing_marked: int
    refusal: str | None


def _covering(race, windows):
    return [
        window
        for window in windows
        if window.effective_department == race.department
        and race.start_date <= window.effective_to
        and race.end_date >= window.effective_from
    ]


def _coherent(window, now):
    return (
        1 <= (window.requested_to - window.requested_from).days + 1 <= 14
        and window.requested_from == window.effective_from
        and window.requested_to == window.effective_to
        and window.requested_department == window.effective_department
        and window.displayed_count == window.distinct_keys
        and window.checked_at <= now
    )


def plan_finalization(inputs):
    """Local builders are new objects; input dataclasses remain entirely unchanged."""
    windows = {window.id: window for window in inputs.windows}
    items = {item.id: item for item in inputs.items}
    races = {race.id: race for race in inputs.races}
    promotions = []
    accepted = set(inputs.accepted)
    for original in inputs.windows:
        if original.status != "partial":
            continue
        changed = False
        for item in inputs.items:
            if (
                item.window_id != original.id
                or item.diagnostic != "stale_observation"
                or item.race_id not in accepted
                or not item.observed
            ):
                continue
            race = races.get(item.race_id)
            if race is None or race.presence != "present":
                continue
            facts = json.loads(race.history_facts)
            observed = json.loads(item.observed)
            observed = {key: observed.get(key) for key in BUSINESS_KEYS}
            if facts["status"] == "cancelled" and observed["status"] == "unknown":
                observed["status"] = "cancelled"
            if observed == facts:
                promoted = replace(item, status="unchanged", diagnostic="historical_duplicate")
                items[item.id] = promoted
                promotions.append(promoted)
                changed = True
        if changed:
            unresolved = sorted(
                {
                    item.diagnostic
                    for item in items.values()
                    if item.window_id == original.id
                    and item.diagnostic not in {None, "historical_duplicate"}
                }
                | ({COVERAGE_UNVERIFIED} & set(original.diagnostics))
            )
            windows[original.id] = replace(
                original,
                status="partial" if unresolved else "success",
                diagnostics=tuple(unresolved),
            )
    for key, window in windows.items():
        if window.status == "success" and not _coherent(window, inputs.now):
            windows[key] = replace(
                window, status="incomplete", diagnostics=(*window.diagnostics, "incoherent_window")
            )
    success = bool(windows) and all(window.status == "success" for window in windows.values())
    if success:
        for race in inputs.races:
            if race.id in accepted:
                continue
            covered = _covering(race, windows.values())
            if covered and all(window.checked_at < race.baseline for window in covered):
                success = False
                for window in covered:
                    previous = windows[window.id]
                    windows[window.id] = replace(
                        previous,
                        status="incomplete",
                        diagnostics=(*previous.diagnostics, "stale_window"),
                    )
    stamps, transitions, affected = [], [], set()
    if success:
        for race in inputs.races:
            if race.id in accepted or race.baseline > inputs.now:
                continue
            covered = _covering(race, windows.values())
            if not covered:
                continue
            stamps.append(
                PresenceStamp(
                    race.id, max(race.baseline, *(window.checked_at for window in covered))
                )
            )
            if race.presence != "to_verify":
                witness = max(covered, key=lambda window: (window.checked_at, window.id))
                transitions.append(
                    AbsenceTransition(
                        race.id,
                        race.presence,
                        race.scope_ids,
                        witness.id,
                        witness.source_url,
                        witness.checked_at,
                        inputs.version,
                    )
                )
                affected.update(window.id for window in covered)
    scope_ids = tuple(
        sorted({scope for transition in transitions for scope in transition.scope_ids})
    )
    refusal = (
        "final_change_capacity"
        if len(scope_ids) > 1000
        else "final_version_mismatch"
        if inputs.version != inputs.supported_version
        else None
    )
    status = "success" if success and refusal is None else "partial" if accepted else "failed"
    return FinalizationPlan(
        tuple(promotions),
        tuple(windows[key] for key in sorted(windows)),
        tuple(stamps),
        tuple(transitions),
        scope_ids,
        tuple(sorted(affected)),
        status,
        len(transitions) if refusal is None else 0,
        refusal,
    )
