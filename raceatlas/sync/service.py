"""Explicit local import with owned transactions and durable, minimal audit.

Independent windows/items can succeed without authorizing absence inference. Only an
entirely successful run may mark absent races to_verify, after global key deduplication.
"""

import hashlib
import re
from contextlib import nullcontext
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from raceatlas.changes import (
    ChangeError,
    canonical,
    record_change,
    scope_guards,
    transaction_connection,
)
from raceatlas.ffc import project_race
from raceatlas.ffc.types import DEPARTMENTS, NORMALIZATION_VERSION, AdapterError, SourceKey
from raceatlas.models import (
    Category,
    Competition,
    EligibilityRule,
    EntryScope,
    ImportItem,
    ImportRun,
    ImportWindow,
    Race,
    SourceAlias,
    SourceRecord,
    SourceRevision,
)
from raceatlas.serialization import race_document

from .change_facts import deltas, snapshot
from .final_plan import (
    BUSINESS_KEYS,
    COVERAGE_UNVERIFIED,
    FinalInputs,
    ItemState,
    RaceState,
    WindowState,
    plan_finalization,
)
from .fingerprint import fingerprint, observation_facts
from .fingerprint import text as clean_text
from .geocoding import Resolution, resolve_commune
from .types import RunResult

LOCK_KEY = 0x5241434541544C


class FinalizationOutcomeUnknown(RuntimeError):
    """No claim about durability; the caller must inspect this run before acting."""

    code = "outcome_unknown"

    def __init__(self, run_id):
        self.run_id = run_id
        super().__init__("Source finalization outcome is unknown")


def _error(code, field="import"):
    raise AdapterError(code, field, "Explicit review or valid complete input required")


def _presence_baseline(race):
    return (
        max(race.source.checked_at, race.source.presence_checked_at or race.source.checked_at),
        race.source_presence,
    )


def _freshness_error(observation, now, baseline=None):
    checked = observation.checked_at
    if not isinstance(checked, datetime) or checked.tzinfo is None or checked.utcoffset() is None:
        return "invalid_timestamp"
    if checked > now:
        return "invalid_timestamp"
    if baseline is not None:
        cutoff, presence = baseline
        # Equal-time evidence cannot disprove an already controlled absence.
        if checked < cutoff or presence != "present" and checked == cutoff:
            return "stale_observation"
    return None


def _index(items):
    result = {}
    for item in items:
        if item.key in result:
            _error("duplicate_input")
        result[item.key] = item
    return result


def _location(commune):
    return (
        {
            "insee_code": commune.insee_code,
            "name": clean_text(commune.name),
            "department": commune.department,
            "coordinates": [commune.longitude, commune.latitude],
        }
        if commune
        else None
    )


def _model_facts(race):
    doc = race_document(race)
    facts = {
        key: doc[key]
        for key in (
            "name",
            "discipline",
            "types",
            "organizer",
            "start_date",
            "end_date",
            "department",
            "status",
        )
    }
    facts["name"], facts["organizer"] = clean_text(facts["name"]), clean_text(facts["organizer"])
    facts["types"] = sorted(facts["types"])
    facts["scopes"] = []
    for scope in doc["entry_scopes"]:
        rules = []
        for rule in scope["rules"]:
            restrictions = rule["restrictions"].copy()
            restrictions["engagers"] = sorted(clean_text(item) for item in restrictions["engagers"])
            restrictions["other_text"] = clean_text(restrictions["other_text"])
            rules.append(
                {"categories": sorted(rule["category_codes"]), "restrictions": restrictions}
            )
        facts["scopes"].append(
            {
                "kind": scope["kind"],
                "eligibility": scope["eligibility_status"],
                "rules": rules,
                "raw_label": clean_text(scope["raw_label"]),
            }
        )
    facts["location"], facts["competition_id"] = _location(race.commune), race.competition_id
    return facts


def _lookup(session, key):
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.provider == "ffc",
            SourceRecord.source_season == key.season,
            SourceRecord.race_number == key.race_number,
        )
    )
    alias = session.scalar(
        select(SourceAlias).where(
            SourceAlias.provider == "ffc",
            SourceAlias.source_season == key.season,
            SourceAlias.race_number == key.race_number,
        )
    )
    if source and alias and source.race_id != alias.race_id:
        _error("source_alias_conflict")
    race_id = source.race_id if source else alias.race_id if alias else None
    return session.get(Race, race_id) if race_id else None, alias


def _alias_target(session, observation, proof, now, *, approved_target=None):
    existing, alias = _lookup(session, observation.key)
    if proof is None:
        return existing, False
    if (
        not proof.evidence_id.strip()
        or proof.decided_at.tzinfo is None
        or proof.decided_at > now
        or proof.key != observation.key
    ):
        _error("invalid_alias_proof")
    if existing and existing.id != proof.race_id:
        _error("source_alias_conflict")
    if alias:
        if alias.evidence_id != proof.evidence_id or alias.decided_at != proof.decided_at:
            _error("source_alias_conflict")
        return existing, False  # Replay of the same durable decision is idempotent.
    target = session.get(Race, proof.race_id)
    if (
        target is None
        or target.source.provider != "ffc"
        or approved_target is not None
        and target.id != approved_target
        or approved_target is None
        and (
            SourceKey(target.source.source_season, target.source.race_number) != proof.expected_key
            or target.revision != proof.expected_revision
        )
    ):
        _error("stale_alias_proof")
    return target, True


def _apply(
    session,
    observation,
    run_id,
    now,
    *,
    alias=None,
    identity=None,
    grouping=None,
    commune=None,
    approved_alias=None,
    baseline=None,
    guard=None,
    allow_incomplete_replay=False,
):
    existing, new_alias = _alias_target(
        session, observation, alias, now, approved_target=approved_alias
    )
    before = None
    if existing is not None:
        if guard is None:
            _error("change_guard_missing")
        guard.check(session, [scope.id for scope in existing.scopes])
        before = snapshot(existing)
    previous_revision = existing.revision if existing else 0
    baseline = baseline or (_presence_baseline(existing) if existing else None)
    freshness_error = _freshness_error(observation, now, baseline)
    if freshness_error:
        _error(freshness_error)
    previous_checked_at = existing.source.checked_at if existing else None
    stale = existing is not None and observation.checked_at < previous_checked_at
    if existing and existing.commune_id and existing.department != observation.department:
        _error("location_identity_needs_review")
    competition_id = existing.competition_id if existing else None
    if grouping:
        replay = False
        if existing and grouping.competition_id == existing.competition_id:
            replay = any(
                item.observed
                and item.observed.get("grouping_evidence") == grouping.evidence_id
                and item.observed.get("grouping_target") == grouping.competition_id
                for item in session.scalars(
                    select(ImportItem).where(
                        ImportItem.race_id == existing.id,
                        ImportItem.status.in_(["created", "updated", "unchanged"]),
                    )
                )
            )
        if (
            not grouping.evidence_id.strip()
            or not replay
            and grouping.expected_revision != (existing.revision if existing else 0)
            or grouping.competition_id is not None
            and session.get(Competition, grouping.competition_id) is None
        ):
            _error("invalid_grouping_proof")
        competition_id = grouping.competition_id
    effective = observation
    if existing and existing.status == "cancelled" and observation.status == "unknown":
        effective = replace(observation, status="cancelled")
    facts = observation_facts(effective)
    facts["competition_id"] = competition_id
    facts["location"] = _location(commune or (existing.commune if existing else None))
    current = _model_facts(existing) if existing else None
    same_facts = existing is not None and fingerprint(current) == fingerprint(facts)
    # Having passed the immutable pre-run cutoff, an older item can only be behind
    # a successful mutation of this run. Identical duplicates never advance evidence.
    if stale and not same_facts:
        _error("stale_observation")
    if existing and (
        observation.diagnostics
        and not (allow_incomplete_replay and same_facts)
        or existing.organizer is not None
        and observation.organizer is None
        or existing.types
        and not observation.types
        or existing.status != "unknown"
        and effective.status == "unknown"
    ):
        _error("incomplete_revision")
    if existing is None:
        model = project_race(effective)
        session.add(model)
        action = "created"
    elif current["scopes"] != facts["scopes"]:
        if identity is None or identity.key != observation.key:
            _error("scope_identity_needs_review")
        canonical = SourceKey(existing.source.source_season, existing.source.race_number)
        projected = project_race(
            replace(effective, key=canonical),
            existing=existing,
            attestation=replace(identity, key=canonical),
        )
        model = session.merge(projected)
        action = "updated"
    else:
        model = existing
        action = "unchanged" if same_facts else "updated"
        for field in (
            "name",
            "discipline",
            "organizer",
            "start_date",
            "end_date",
            "department",
            "status",
        ):
            if not stale:
                setattr(model, field, getattr(effective, field))
        # Type replacement is safe only within the same discipline. Other changes need review.
        if {item.code for item in existing.types} != set(observation.types):
            _error("sport_identity_needs_review")
    model.competition_id = competition_id
    if commune:
        model.commune = commune
    # A projected scope update may already carry the new page timestamp after merge.
    # Advance its matching presence evidence before the first constraint-checked flush.
    if not stale:
        model.source.presence_checked_at = observation.checked_at
    with session.no_autoflush:
        codes = {
            item.category_code
            for scope in model.scopes
            for rule in scope.rules
            for item in rule.categories
        }
        for code in codes:
            if session.get(Category, code) is None:
                session.add(Category(code=code, label=code))
    session.flush()
    if existing is not None and action == "updated":
        model.revision = previous_revision + 1
    if new_alias or existing is None:
        session.add(
            SourceAlias(
                source_season=observation.key.season,
                race_number=observation.key.race_number,
                race_id=model.id,
                evidence_id=alias.evidence_id if alias else "initial-" + run_id,
                decided_at=alias.decided_at if alias else now,
            )
        )
    if new_alias:
        model.source.source_season = observation.key.season
        model.source.race_number = observation.key.race_number
    if not stale:
        model.source.checked_at, model.source.source_url = (
            observation.checked_at,
            observation.source_url,
        )
        model.source_presence = "present"
    revision = None
    if action != "unchanged":
        revision = SourceRevision(
            race_id=model.id,
            run_id=run_id,
            revision=model.revision,
            business_hash=fingerprint(facts),
            facts=facts,
            normalization_version=observation.normalization_version,
            source_url=observation.source_url,
            checked_at=observation.checked_at,
        )
        session.add(revision)
    session.flush()
    if before is not None:
        after = snapshot(model)
        if action == "updated":
            record_change(
                session,
                guard,
                race_id=model.id,
                event_key="revision:" + revision.id,
                kind="business",
                targets=deltas(before, after),
                provenance={
                    "source_url": revision.source_url,
                    "checked_at": revision.checked_at.isoformat(),
                    "normalization_version": revision.normalization_version,
                },
            )
        if before.presence != "present" and after.presence == "present":
            identity = f"{run_id}:{model.id}:restore:{before.presence}:present"
            record_change(
                session,
                guard,
                race_id=model.id,
                event_key="presence:" + hashlib.sha256(identity.encode("utf-8")).hexdigest(),
                kind="presence",
                targets={
                    scope_id: {
                        "before": {"source_presence": before.presence},
                        "after": {"source_presence": "present"},
                    }
                    for scope_id, _ in after.scopes
                },
                provenance={
                    "source_url": observation.source_url,
                    "checked_at": observation.checked_at.isoformat(),
                    "normalization_version": observation.normalization_version,
                    "evidence_id": "run:" + run_id,
                },
            )
    return model.id, action


def _window_valid(calendar, now):
    return (
        calendar.status == "consistent_sample"
        and calendar.normalization_version == NORMALIZATION_VERSION
        and not calendar.diagnostics
        and calendar.checked_at.tzinfo is not None
        and calendar.checked_at <= now
        and calendar.requested.start == calendar.effective_start
        and calendar.requested.end == calendar.effective_end
        and calendar.requested.department == calendar.effective_department
        and calendar.effective_department in DEPARTMENTS
        and 1 <= (calendar.effective_end - calendar.effective_start).days + 1 <= 14
        and calendar.displayed_count == len(set(calendar.keys)) == len(calendar.keys)
    )


@dataclass
class _Preflight:
    conflicts: set
    errors: dict
    targets: dict
    approved_aliases: dict
    baselines: dict


def _preflight(session, batches, now):
    """Resolve all identities against one baseline before the first catalogue mutation.

    A proof can introduce a reference to an existing ID, but neither names nor ordering
    create identity. Proofs valid only after another window mutates the baseline are refused.
    """
    groups, key_groups, targets, approved, errors = {}, {}, {}, {}, {}
    new_aliases = {}
    baselines = {}
    for batch in batches:
        locations = {fact.key: fact for fact in batch.locations}
        groupings = {proof.key: proof for proof in batch.competitions}
        aliases = {proof.key: proof for proof in batch.aliases}
        identities = {proof.key: proof for proof in batch.identities}
        for observation in batch.details:
            key = observation.key
            target = None
            try:
                target, _ = _lookup(session, key)
                if key in aliases:
                    target, is_new = _alias_target(session, observation, aliases[key], now)
                    approved[key] = target.id
                    if is_new:
                        new_aliases.setdefault(target.id, set()).add(key)
            except AdapterError as error:
                errors[key] = error.diagnostic.code
            location, grouping = locations.get(key), groupings.get(key)
            identity_proof = identities.get(key)
            scope_ids = dict(identity_proof.scope_ids) if identity_proof else {}
            rule_ids = dict(identity_proof.rule_ids) if identity_proof else {}
            signature = fingerprint(
                {
                    "facts": observation_facts(observation),
                    "location": {
                        "name": clean_text(location.commune_name).casefold()
                        if isinstance(location.commune_name, str)
                        else None,
                        "insee_code": location.insee_code,
                        "department": location.department,
                    }
                    if location
                    else None,
                    "group": grouping.competition_id
                    if grouping
                    else target.competition_id
                    if target
                    else None,
                    "identity_assignment": [
                        [
                            scope_ids.get(scope.token),
                            [rule_ids.get(rule.token) for rule in scope.rules],
                        ]
                        for scope in observation.scopes
                    ]
                    if identity_proof
                    else None,
                }
            )
            identity = ("race", target.id) if target else ("source", key)
            groups.setdefault(identity, []).append((key, signature))
            key_groups.setdefault(key, set()).add((identity, signature))
            if target:
                targets[key] = target.id
                baselines.setdefault(target.id, _presence_baseline(target))
    conflicts = {key for key, signatures in key_groups.items() if len(signatures) > 1}
    for key, entries in key_groups.items():
        if len({identity for identity, _ in entries}) > 1:
            # Conflicting identity claims must not make the audit assert an arbitrary owner.
            targets.pop(key, None)
            approved.pop(key, None)
    for identity, entries in groups.items():
        keys = {key for key, _ in entries}
        if len({signature for _, signature in entries}) > 1:
            conflicts.update(keys)
        if identity[0] == "race" and len(new_aliases.get(identity[1], ())) > 1:
            # Each new alias proof also changes the primary source reference. Competing
            # primary-reference decisions cannot be selected by window processing order.
            conflicts.update(keys)
    return _Preflight(conflicts, errors, targets, approved, baselines)


def _import_window(
    session,
    batch,
    run_id,
    now,
    provider,
    preflight,
    *,
    guard=None,
    guard_error=False,
    positive_only=False,
):
    calendar = batch.calendar
    window = ImportWindow(
        run_id=run_id,
        requested_from=calendar.requested.start,
        requested_to=calendar.requested.end,
        effective_from=calendar.effective_start,
        effective_to=calendar.effective_end,
        requested_department=calendar.requested.department,
        effective_department=calendar.effective_department,
        displayed_count=calendar.displayed_count,
        distinct_keys=len(set(calendar.keys)),
        status="success",
        diagnostics=[],
        source_url=calendar.source_url,
        checked_at=calendar.checked_at,
    )
    session.add(window)
    session.flush()
    if guard_error:
        window.status, window.diagnostics = "failed", ["change_guard_unavailable"]
        return "failed", set()
    if not _window_valid(calendar, now):
        window.status, window.diagnostics = (
            "incomplete",
            ["incoherent_window", *(item.code for item in calendar.diagnostics)],
        )
        return "incomplete", set()
    try:
        details, locations = _index(batch.details), _index(batch.locations)
        aliases, groupings = _index(batch.aliases), _index(batch.competitions)
        identities = _index(batch.identities)
        failures = _index(batch.failures)
        if any(
            not isinstance(failure.code, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", failure.code)
            for failure in failures.values()
        ):
            _error("invalid_detail_failure")
        if set(details) - set(calendar.keys):
            _error("unexpected_detail")
        if set(failures) - set(calendar.keys) or set(failures) & set(details):
            _error("conflicting_detail_failure")
        if any(
            set(bindings) - set(details) for bindings in (locations, aliases, groupings, identities)
        ):
            _error("unexpected_binding")
    except AdapterError as error:
        window.status, window.diagnostics = "failed", [error.diagnostic.code]
        return "failed", set()
    present, codes = set(), []
    for key in calendar.keys:
        observation = details.get(key)
        code, race_id, action = None, None, "error"
        freshness_error = (
            _freshness_error(observation, now, preflight.baselines.get(preflight.targets.get(key)))
            if observation
            else None
        )
        if observation is None:
            code = failures[key].code if key in failures else "missing_detail"
        elif key in preflight.conflicts:
            code = "conflicting_details"
            race_id, action = preflight.targets.get(key), "review"
        elif key in preflight.errors:
            code, action = preflight.errors[key], "review"
            race_id = preflight.targets.get(key)
        elif freshness_error == "invalid_timestamp":
            code, race_id = freshness_error, preflight.targets.get(key)
        elif observation.normalization_version != NORMALIZATION_VERSION:
            code = "unsupported_normalization"
        elif observation.checked_at < calendar.checked_at:
            code = "stale_detail"
        elif observation.department != calendar.effective_department or not (
            observation.start_date <= calendar.effective_end
            and observation.end_date >= calendar.effective_start
        ):
            code = "detail_outside_window"
        elif freshness_error:
            code, race_id = freshness_error, preflight.targets.get(key)
        else:
            resolution = Resolution("negative", None, None, False)
            try:
                if key in locations:
                    if locations[key].department != observation.department:
                        _error("location_department_mismatch")
                    if provider is None:
                        _error("provider_unavailable")
                    with session.begin_nested():
                        resolution = resolve_commune(session, locations[key], provider, now)
                    if resolution.status == "error":
                        _error(resolution.diagnostic, "geocoding")
                with session.begin_nested():
                    race_id, action = _apply(
                        session,
                        observation,
                        run_id,
                        now,
                        alias=aliases.get(key),
                        identity=identities.get(key),
                        grouping=groupings.get(key),
                        commune=resolution.commune,
                        approved_alias=preflight.approved_aliases.get(key),
                        baseline=preflight.baselines.get(preflight.targets.get(key)),
                        guard=guard,
                        allow_incomplete_replay=positive_only,
                    )
                present.add(race_id)
            except AdapterError as error:
                code = error.diagnostic.code
                action = (
                    "review"
                    if "review" in code or "proof" in code or "conflict" in code
                    else "error"
                )
            except SQLAlchemyError:
                code, action = "storage_error", "error"
            except ChangeError:
                code, action = "change_record_error", "error"
        if code:
            codes.append(code)
        observed = observation_facts(observation) if observation else None
        if observed is not None and key in locations:
            fact = locations[key]
            observed["location_fact"] = {
                "name": fact.commune_name,
                "department": fact.department,
                "insee_code": fact.insee_code,
                "evidence_id": fact.evidence_id,
            }
            if provider is not None:
                observed["geocoding_provider"] = {
                    "name": provider.name,
                    "version": provider.version,
                }
        if observed is not None and key in identities:
            observed["identity_evidence"] = identities[key].evidence_id
        if observed is not None and key in groupings:
            observed["grouping_evidence"] = groupings[key].evidence_id
            observed["grouping_target"] = groupings[key].competition_id
        if observed is not None and action == "review":
            observed["identity_status"] = "needs_review"
        session.add(
            ImportItem(
                window_id=window.id,
                source_season=key.season,
                race_number=key.race_number,
                race_id=race_id,
                status=action,
                diagnostic=code,
                observed=observed,
            )
        )
    if positive_only:
        codes.append(COVERAGE_UNVERIFIED)
    window.status = "partial" if codes else "success"
    window.diagnostics = sorted(set(codes))
    session.flush()
    return window.status, present


def _utc(value):
    return value.astimezone(timezone.utc) if value is not None else None


def _load_final_inputs(session, run_id, now, accepted):
    """Read-only hydration; the returned immutable values retain no ORM references."""
    with session.no_autoflush:
        run = session.get(ImportRun, run_id)
        windows = list(
            session.scalars(
                select(ImportWindow).where(ImportWindow.run_id == run_id).order_by(ImportWindow.id)
            )
        )
        items = list(
            session.scalars(
                select(ImportItem)
                .join(ImportWindow)
                .where(ImportWindow.run_id == run_id)
                .order_by(ImportItem.id)
            )
        )
        historical = {
            item.race_id
            for item in items
            if item.diagnostic == "stale_observation" and item.race_id in accepted and item.observed
        }
        candidates = list(
            session.scalars(
                select(Race)
                .join(SourceRecord)
                .where(SourceRecord.provider == "ffc")
                .options(
                    joinedload(Race.source),
                    joinedload(Race.commune),
                    selectinload(Race.types),
                    selectinload(Race.scopes)
                    .selectinload(EntryScope.rules)
                    .selectinload(EligibilityRule.categories),
                )
                .order_by(Race.id)
            )
        )
        window_values = tuple(
            WindowState(
                window.id,
                window.status,
                tuple(window.diagnostics),
                window.requested_from,
                window.requested_to,
                window.effective_from,
                window.effective_to,
                window.requested_department,
                window.effective_department,
                window.displayed_count,
                window.distinct_keys,
                window.source_url,
                _utc(window.checked_at),
            )
            for window in windows
        )
        item_values = tuple(
            ItemState(
                item.id,
                item.window_id,
                item.race_id,
                item.status,
                item.diagnostic,
                canonical(item.observed) if item.observed else None,
            )
            for item in items
        )
        race_values = []
        for race in candidates:
            facts = _model_facts(race) if race.id in historical else None
            race_values.append(
                RaceState(
                    race.id,
                    race.revision,
                    race.department,
                    race.start_date,
                    race.end_date,
                    race.source_presence,
                    _utc(race.source.checked_at),
                    _utc(race.source.presence_checked_at),
                    tuple(sorted(scope.id for scope in race.scopes)),
                    canonical({key: facts[key] for key in BUSINESS_KEYS}) if facts else b"{}",
                )
            )
    return FinalInputs(
        run_id,
        run.parser_version,
        NORMALIZATION_VERSION,
        _utc(now),
        tuple(sorted(accepted)),
        window_values,
        item_values,
        tuple(race_values),
    )


def _apply_finalization(session, run_id, now, plan, guard):
    for item in plan.items:
        model = session.get(ImportItem, item.id)
        model.status, model.diagnostic = item.status, item.diagnostic
    for window in plan.windows:
        model = session.get(ImportWindow, window.id)
        model.status, model.diagnostics = window.status, list(window.diagnostics)
    for stamp in plan.stamps:
        session.get(Race, stamp.race_id).source.presence_checked_at = stamp.at
    for transition in plan.transitions:
        session.get(Race, transition.race_id).source_presence = "to_verify"
    for transition in plan.transitions:
        identity = canonical(
            (
                run_id,
                transition.race_id,
                "absence",
                transition.before,
                "to_verify",
                transition.witness_window_id,
            )
        )
        record_change(
            session,
            guard,
            race_id=transition.race_id,
            event_key="presence:" + hashlib.sha256(identity).hexdigest(),
            kind="presence",
            targets={
                scope: {
                    "before": {"source_presence": transition.before},
                    "after": {"source_presence": "to_verify"},
                }
                for scope in transition.scope_ids
            },
            provenance={
                "source_url": transition.source_url,
                "checked_at": transition.checked_at.isoformat(),
                "normalization_version": transition.version,
                "evidence_id": "window:" + transition.witness_window_id,
            },
        )
    run = session.get(ImportRun, run_id)
    run.status, run.finished_at, run.missing_marked = plan.run_status, now, plan.missing_marked


def _audit_final_refusal(session, run_id, now, accepted, reason, affected):
    run = session.get(ImportRun, run_id)
    run.status, run.finished_at, run.missing_marked = "partial" if accepted else "failed", now, 0
    windows = session.scalars(select(ImportWindow).where(ImportWindow.run_id == run_id)).all()
    for window in windows:
        if not affected or window.id in affected:
            if window.status != "failed":
                window.status = "incomplete"
            window.diagnostics = list(dict.fromkeys([*window.diagnostics, reason]))


def _confirm_final_commit(engine, run_id, now, accepted, affected):
    """Resolve the old row lock before concluding that a commit did not happen.

    This is a new checkout/transaction, never the failed Session's identity map.
    The terminal audit row was flushed atomically with all final facts/events.
    """
    try:
        with engine.connect().execution_options(isolation_level="READ COMMITTED") as connection:
            with Session(connection) as confirmation:
                confirmation.execute(text("SET LOCAL statement_timeout='3000ms'"))
                confirmation.execute(text("SET LOCAL lock_timeout='3000ms'"))
                row = confirmation.execute(
                    select(ImportRun.status, ImportRun.finished_at, ImportRun.missing_marked)
                    .where(ImportRun.id == run_id)
                    .with_for_update()
                ).one_or_none()
                if (
                    row
                    and row.finished_at is not None
                    and row.status
                    in {
                        "success",
                        "partial",
                        "failed",
                    }
                ):
                    return RunResult(run_id, row.status, row.missing_marked)
                if (
                    not row
                    or row.status != "running"
                    or row.finished_at is not None
                    or row.missing_marked != 0
                ):
                    raise FinalizationOutcomeUnknown(run_id)
                # FOR UPDATE has resolved any in-flight terminal write. No commit
                # was durable; only now may a refusal audit replace running.
                _audit_final_refusal(
                    confirmation, run_id, now, accepted, "final_commit_error", affected
                )
                confirmation.flush()
                run = confirmation.get(ImportRun, run_id)
                result = RunResult(run_id, run.status, run.missing_marked)
                confirmation.commit()
                return result
    except SQLAlchemyError:
        # Includes a lost acknowledgement for this refusal audit: its outcome
        # is unknown too. Never replay the source mutation or invent a result.
        raise FinalizationOutcomeUnknown(run_id) from None


def _commit_finalization(session, engine, run_id, now, accepted, affected):
    run = session.get(ImportRun, run_id)
    result = RunResult(run_id, run.status, run.missing_marked)
    connection = session.get_bind()
    try:
        session.commit()
        return result
    except SQLAlchemyError:
        try:
            session.rollback()
        except SQLAlchemyError:
            # Public Connection API closes the unusable DBAPI connection. The
            # confirmation row lock still protects against a server-side COMMIT
            # completing after this local failure/disconnect.
            connection.invalidate()
        return _confirm_final_commit(engine, run_id, now, accepted, affected)


def _finish_run(session, run_id, now, accepted, *, engine):
    """Owned only by synchronize: one final commit, or rollback then refusal audit."""
    plan, reason = None, "final_plan_invalid"
    try:
        transaction_connection(session)
        inputs = _load_final_inputs(session, run_id, now, accepted)
        plan = plan_finalization(inputs)
        if plan.refusal:
            reason = plan.refusal
            raise ChangeError("Finalization refused")
        reason = "change_guard_unavailable"
        session.execute(text("SET LOCAL lock_timeout='3000ms'"))
        with (
            scope_guards(session, plan.scope_ids) if plan.scope_ids else nullcontext(None) as guard
        ):
            session.expire_all()
            if _load_final_inputs(session, run_id, now, accepted) != inputs:
                reason = "final_state_changed"
                raise ChangeError("Finalization snapshot changed")
            reason = "change_record_error"
            _apply_finalization(session, run_id, now, plan, guard)
            # Separate known precommit failures from ambiguous commit errors.
            # The terminal ImportRun row lock must exist before attempting COMMIT.
            reason = "final_flush_error"
            session.flush()
    except (ChangeError, SQLAlchemyError):
        session.rollback()
        _audit_final_refusal(
            session, run_id, now, accepted, reason, plan.affected_windows if plan else ()
        )
        session.flush()
    return _commit_finalization(
        session, engine, run_id, now, accepted, plan.affected_windows if plan else ()
    )


def _window_scope_ids(session, batch, preflight):
    """Current inventory, including races created by an earlier committed window."""
    scope_ids = set()
    with session.no_autoflush:
        for key in batch.calendar.keys:
            try:
                existing, _ = _lookup(session, key)
            except AdapterError:
                continue  # The existing preflight/item audit retains this identity error.
            if existing is None:
                target = preflight.approved_aliases.get(key) or preflight.targets.get(key)
                existing = session.get(Race, target) if target else None
            if existing is not None:
                scope_ids.update(scope.id for scope in existing.scopes)
    return scope_ids


def synchronize(engine, batches, *, checked_at=None, provider=None, synthetic=True):
    """Own all transactions. No caller Session is accepted or implicitly committed.

    This V1 development entry point deliberately permits only explicit local databases.
    Audit cannot be guaranteed if PostgreSQL itself is unavailable; errors propagate.
    """
    if engine.url.host not in {"127.0.0.1", "localhost", "::1"}:
        _error("local_database_required")
    return _synchronize(
        engine, batches, checked_at=checked_at, provider=provider, synthetic=synthetic
    )


def bootstrap_catalog_2027(engine, batches, *, target_host, target_database, provider=None):
    """Apply verified positive observations to the operator's explicit Neon target."""
    url = engine.url
    if (
        url.drivername != "postgresql+psycopg"
        or url.host != target_host
        or not isinstance(target_host, str)
        or not re.fullmatch(r"ep-[a-z0-9-]+\.[a-z0-9.-]+\.neon\.tech", target_host)
        or "-pooler." in target_host
        or url.database != target_database
        or not target_database
        or url.port not in (None, 5432)
        or url.query.get("sslmode") != "verify-full"
        or set(url.query) - {"sslmode", "sslrootcert", "channel_binding"}
    ):
        _error("invalid_bootstrap_database")
    batches = tuple(batches)
    if not batches or any(
        batch.calendar.requested.start.year != 2027
        or batch.calendar.requested.end.year != 2027
        or batch.aliases
        or batch.competitions
        or batch.identities
        or any(observation.start_date.year != 2027 for observation in batch.details)
        for batch in batches
    ):
        _error("invalid_bootstrap_scope")
    return _synchronize(engine, batches, provider=provider, synthetic=False, positive_only=True)


def _synchronize(
    engine, batches, *, checked_at=None, provider=None, synthetic, positive_only=False
):
    now = checked_at or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        _error("invalid_timestamp")
    batches = tuple(batches)
    with engine.connect() as connection:
        locked = connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_KEY})
        connection.commit()
        if not locked:
            _error("import_busy")
        try:
            with Session(connection) as session:
                try:
                    transaction_connection(session)
                except ChangeError:
                    _error("invalid_source_transaction")
                preflight = _preflight(session, batches, now)
                run = ImportRun(
                    started_at=now,
                    status="running",
                    parser_version=NORMALIZATION_VERSION,
                    synthetic=synthetic,
                    missing_marked=0,
                )
                session.add(run)
                session.commit()
                run_id, present = run.id, set()
                for batch in batches:
                    scope_ids = _window_scope_ids(session, batch, preflight)
                    session.execute(text("SET LOCAL lock_timeout='3000ms'"))
                    try:
                        with (
                            scope_guards(session, scope_ids)
                            if scope_ids
                            else nullcontext(None) as guard
                        ):
                            # Inventory/preflight may have populated the identity map before
                            # waiting. Reload under the lock before taking immutable facts.
                            session.expire_all()
                            _, seen = _import_window(
                                session,
                                batch,
                                run_id,
                                now,
                                provider,
                                preflight,
                                guard=guard,
                                positive_only=positive_only,
                            )
                    except (ChangeError, OperationalError):
                        session.rollback()
                        _, seen = _import_window(
                            session,
                            batch,
                            run_id,
                            now,
                            provider,
                            preflight,
                            guard_error=True,
                            positive_only=positive_only,
                        )
                    present.update(seen)
                    session.commit()
                return _finish_run(session, run_id, now, present, engine=engine)
        finally:
            try:
                if connection.in_transaction():
                    connection.rollback()
                # An invalidated DBAPI connection has been closed: its session
                # advisory lock is released by PostgreSQL. Do not reconnect just
                # to unlock another physical connection, or mask outcome_unknown.
                if not connection.invalidated and not connection.closed:
                    connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
                    connection.commit()
            except SQLAlchemyError:
                connection.invalidate()
