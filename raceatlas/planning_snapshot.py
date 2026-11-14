"""One READ COMMITTED graph SELECT, scoped DTOs, and exact bounded UTF-8 responses."""

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import joinedload, raiseload

from raceatlas.models import EligibilityRule, EntryScope, Race, SavedEntry
from raceatlas.planning import PlanningNotFound, _actor_id, _target_id
from raceatlas.serialization import timestamp


class PlanningLimitError(ValueError):
    def __init__(self):
        super().__init__("Personal selection exceeds limits.")


@dataclass(frozen=True)
class PlanningLimits:
    saved_entries: int = 1000
    response_bytes: int = 2 * 1024 * 1024
    text_bytes: int = 16 * 1024
    events: int = 1000
    cache_pairs: int = 10000

    def __post_init__(self):
        if any(
            type(value) is not int or not 1 <= value <= maximum
            for value, maximum in (
                (self.saved_entries, 1000),
                (self.response_bytes, 2 * 1024 * 1024),
                (self.text_bytes, 16 * 1024),
                (self.events, 1000),
                (self.cache_pairs, 10000),
            )
        ):
            raise ValueError("Invalid personal selection limits.")


def _document(saved, race):
    scope = saved.scope
    commune = race.commune
    location = (
        None
        if commune is None
        else {
            "commune_id": commune.id,
            "insee_code": commune.insee_code,
            "commune_name": commune.name,
            "department": commune.department,
            "coordinates": None
            if commune.longitude is None
            else [commune.longitude, commune.latitude],
            "precision": commune.precision,
            "provenance": commune.provenance,
            "geocoded_at": timestamp(commune.geocoded_at),
        }
    )
    return {
        "id": saved.id,
        "scope_id": saved.scope_id,
        "status": saved.status,
        "revision": saved.revision,
        "created_at": timestamp(saved.created_at),
        "updated_at": timestamp(saved.updated_at),
        "race": {
            "id": race.id,
            "competition_id": race.competition_id,
            "name": race.name,
            "discipline": race.discipline,
            "types": [value.code for value in race.types],
            "organizer": race.organizer,
            "start_date": race.start_date.isoformat(),
            "end_date": race.end_date.isoformat(),
            "department": race.department,
            "status": race.status,
            "source_presence": race.source_presence,
            "revision": race.revision,
            "location": location,
            "personal_eligibility": "not_evaluated",
            "source": {
                "provider": race.source.provider,
                "source_season": race.source.source_season,
                "race_number": race.source.race_number,
                "source_url": race.source.source_url,
                "checked_at": timestamp(race.source.checked_at),
            },
        },
        "scope": {
            "id": scope.id,
            "kind": scope.kind,
            "source_list_id": scope.source_list_id,
            "identity_status": scope.identity_status,
            "eligibility_status": scope.eligibility_status,
            "raw_label": scope.raw_label,
            "rules": [
                {
                    "id": rule.id,
                    "category_codes": [value.category_code for value in rule.categories],
                    "raw_label": rule.raw_label,
                    "evidence_id": rule.evidence_id,
                    "normalization_version": rule.normalization_version,
                    "restrictions": {
                        name: getattr(rule, name)
                        for name in (
                            "sex",
                            "min_age",
                            "max_age",
                            "age_reference",
                            "age_season",
                            "engagers",
                            "other_text",
                        )
                    },
                }
                for rule in scope.rules
            ],
        },
    }


def snapshot_documents(session, actor, *, entry_id=None, limits=None, calendar_only=False):
    limits = PlanningLimits() if limits is None else limits
    account_id = _actor_id(session, actor)
    statement = (
        select(SavedEntry, Race)
        .join(EntryScope, SavedEntry.scope_id == EntryScope.id)
        .join(Race, Race.id == EntryScope.race_id)
        .where(SavedEntry.account_id == account_id)
        .options(
            raiseload("*"),
            joinedload(SavedEntry.scope)
            .joinedload(EntryScope.rules)
            .joinedload(EligibilityRule.categories),
            joinedload(Race.commune),
            joinedload(Race.types),
            joinedload(Race.source),
        )
        .order_by(SavedEntry.created_at, SavedEntry.id)
        .execution_options(populate_existing=True, planning_graph_snapshot=True)
    )
    if calendar_only:
        statement = statement.where(SavedEntry.status.in_(("planned", "registered")))
    if entry_id is not None:
        statement = statement.where(SavedEntry.id == _target_id(entry_id)).limit(1)
    else:
        statement = statement.limit(limits.saved_entries + 1)
    rows = session.execute(statement).unique().all()
    if entry_id is not None and not rows:
        raise PlanningNotFound()
    if entry_id is None and len(rows) > limits.saved_entries:
        raise PlanningLimitError()
    # All relationships consumed here were joined in the SAME statement snapshot.
    return [_document(saved, race) for saved, race in rows]


def encode_personal(document, limits):
    def check(value):
        if isinstance(value, str):
            try:
                oversized = len(value.encode("utf-8")) > limits.text_bytes
            except UnicodeEncodeError:
                oversized = True
            if oversized:
                raise PlanningLimitError()
        elif isinstance(value, dict):
            for item in value.values():
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)

    check(document)
    try:
        result = json.dumps(
            document, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (ValueError, UnicodeEncodeError):
        raise PlanningLimitError() from None
    if len(result) > limits.response_bytes:
        raise PlanningLimitError()
    return result
