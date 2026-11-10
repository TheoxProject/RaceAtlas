"""Explicit local import with owned transactions and durable, minimal audit.

Independent windows/items can succeed without authorizing absence inference. Only an
entirely successful run may mark absent races to_verify, after global key deduplication.
"""

import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from raceatlas.ffc import project_race
from raceatlas.ffc.types import DEPARTMENTS, NORMALIZATION_VERSION, AdapterError, SourceKey
from raceatlas.models import (
    Category,
    Competition,
    ImportItem,
    ImportRun,
    ImportWindow,
    Race,
    SourceAlias,
    SourceRecord,
    SourceRevision,
)
from raceatlas.serialization import race_document

from .fingerprint import fingerprint, observation_facts
from .fingerprint import text as clean_text
from .geocoding import Resolution, resolve_commune
from .types import RunResult

LOCK_KEY = 0x5241434541544C


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
):
    existing, new_alias = _alias_target(
        session, observation, alias, now, approved_target=approved_alias
    )
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
    # Having passed the immutable pre-run cutoff, an older item can only be behind
    # a successful mutation of this run. Identical duplicates never advance evidence.
    if stale and fingerprint(current) != fingerprint(facts):
        _error("stale_observation")
    if existing and (
        observation.diagnostics
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
        action = "unchanged" if fingerprint(current) == fingerprint(facts) else "updated"
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
    if action != "unchanged":
        session.add(
            SourceRevision(
                race_id=model.id,
                run_id=run_id,
                revision=model.revision,
                business_hash=fingerprint(facts),
                facts=facts,
                normalization_version=observation.normalization_version,
                source_url=observation.source_url,
                checked_at=observation.checked_at,
            )
        )
    session.flush()
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


def _import_window(session, batch, run_id, now, provider, preflight):
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
    window.status = "partial" if codes else "success"
    window.diagnostics = sorted(set(codes))
    session.flush()
    return window.status, present


def _finalize_historical_duplicates(session, windows, accepted):
    """Historical records never mutate data; only an actual successful item of this run
    can make an identical historical record an ignored duplicate instead of a failure.
    """
    business_keys = (
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
    for window in windows:
        if window.status != "partial":
            continue
        items = list(session.scalars(select(ImportItem).where(ImportItem.window_id == window.id)))
        changed = False
        for item in items:
            if (
                item.diagnostic != "stale_observation"
                or item.race_id not in accepted
                or not item.observed
            ):
                continue
            race = session.get(Race, item.race_id)
            current = _model_facts(race)
            observed = {key: item.observed.get(key) for key in business_keys}
            if current["status"] == "cancelled" and observed["status"] == "unknown":
                observed["status"] = "cancelled"
            if race.source_presence == "present" and observed == {
                key: current[key] for key in business_keys
            }:
                item.status, item.diagnostic = "unchanged", "historical_duplicate"
                changed = True
        if changed:
            unresolved = {
                item.diagnostic
                for item in items
                if item.diagnostic not in {None, "historical_duplicate"}
            }
            window.status = "partial" if unresolved else "success"
            window.diagnostics = sorted(unresolved)


def synchronize(engine, batches, *, checked_at=None, provider=None, synthetic=True):
    """Own all transactions. No caller Session is accepted or implicitly committed.

    This V1 development entry point deliberately permits only explicit local databases.
    Audit cannot be guaranteed if PostgreSQL itself is unavailable; errors propagate.
    """
    if engine.url.host not in {"127.0.0.1", "localhost", "::1"}:
        _error("local_database_required")
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
                    _, seen = _import_window(session, batch, run_id, now, provider, preflight)
                    present.update(seen)
                    session.commit()
                run = session.get(ImportRun, run_id)
                candidates = list(
                    session.scalars(
                        select(Race).join(SourceRecord).where(SourceRecord.provider == "ffc")
                    )
                )
                windows = list(
                    session.scalars(select(ImportWindow).where(ImportWindow.run_id == run_id))
                )
                _finalize_historical_duplicates(session, windows, present)
                success = bool(windows) and all(window.status == "success" for window in windows)
                # Old empty windows cannot override newer verified observations. Defer all
                # absence inference for this run when any candidate has only stale coverage.
                if success:
                    for race in candidates:
                        if race.id in present:
                            continue
                        covering = [
                            window
                            for window in windows
                            if (
                                window.effective_department == race.department
                                and race.start_date <= window.effective_to
                                and race.end_date >= window.effective_from
                            )
                        ]
                        if covering and all(
                            window.checked_at < _presence_baseline(race)[0] for window in covering
                        ):
                            success = False
                            for window in covering:
                                window.status = "incomplete"
                                window.diagnostics = [*window.diagnostics, "stale_window"]
                if success:
                    for race in candidates:
                        if race.id in present or _presence_baseline(race)[0] > now:
                            continue
                        covered = [
                            window
                            for window in windows
                            if (
                                race.department == window.effective_department
                                and race.start_date <= window.effective_to
                                and race.end_date >= window.effective_from
                            )
                        ]
                        if covered:
                            race.source.presence_checked_at = max(
                                _presence_baseline(race)[0],
                                *(window.checked_at for window in covered),
                            )
                            if race.source_presence != "to_verify":
                                race.source_presence = "to_verify"
                                run.missing_marked += 1
                run.status = "success" if success else "partial" if present else "failed"
                run.finished_at = now
                result = RunResult(run_id, run.status, run.missing_marked)
                session.commit()
                return result
        finally:
            if connection.in_transaction():
                connection.rollback()
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
            connection.commit()
