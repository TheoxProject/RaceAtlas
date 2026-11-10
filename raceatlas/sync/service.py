"""Explicit local import with owned transactions and durable, minimal audit.

Independent windows/items can succeed without authorizing absence inference. Only an
entirely successful run may mark absent races to_verify, after global key deduplication.
"""

from dataclasses import replace
from datetime import date, datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from raceatlas.ffc import project_race
from raceatlas.ffc.types import NORMALIZATION_VERSION, AdapterError, SourceKey
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


def _alias_target(session, observation, proof, now):
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
        or SourceKey(target.source.source_season, target.source.race_number) != proof.expected_key
        or target.revision != proof.expected_revision
    ):
        _error("stale_alias_proof")
    return target, True


def _apply(
    session, observation, run_id, now, *, alias=None, identity=None, grouping=None, commune=None
):
    if observation.checked_at.tzinfo is None or observation.checked_at > now:
        _error("invalid_timestamp")
    existing, new_alias = _alias_target(session, observation, alias, now)
    previous_revision = existing.revision if existing else 0
    if existing and observation.checked_at < existing.source.checked_at:
        _error("stale_observation")
    if existing and existing.commune_id and existing.department != observation.department:
        _error("location_identity_needs_review")
    competition_id = existing.competition_id if existing else None
    if grouping:
        if (
            not grouping.evidence_id.strip()
            or grouping.expected_revision != (existing.revision if existing else 0)
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
            setattr(model, field, getattr(effective, field))
        # Type replacement is safe only within the same discipline. Other changes need review.
        if {item.code for item in existing.types} != set(observation.types):
            _error("sport_identity_needs_review")
    model.competition_id = competition_id
    if commune:
        model.commune = commune
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
        and not calendar.diagnostics
        and calendar.checked_at.tzinfo is not None
        and calendar.checked_at <= now
        and calendar.requested.start == calendar.effective_start
        and calendar.requested.end == calendar.effective_end
        and calendar.requested.department == calendar.effective_department
        and 1 <= (calendar.effective_end - calendar.effective_start).days + 1 <= 14
        and calendar.displayed_count == len(set(calendar.keys)) == len(calendar.keys)
    )


def _import_window(session, batch, run_id, now, provider, conflicts):
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
        window.status, window.diagnostics = "incomplete", ["incoherent_window"]
        return "incomplete", set()
    try:
        details, locations = _index(batch.details), _index(batch.locations)
        aliases, groupings = _index(batch.aliases), _index(batch.competitions)
        identities = _index(batch.identities)
        if set(details) - set(calendar.keys):
            _error("unexpected_detail")
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
        if observation is None:
            code = "missing_detail"
        elif key in conflicts:
            code = "conflicting_details"
        elif observation.department != calendar.effective_department or not (
            observation.start_date <= calendar.effective_end
            and observation.end_date >= calendar.effective_start
        ):
            code = "detail_outside_window"
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
                    )
                present.add(race_id)
                if resolution.status == "error":
                    code = resolution.diagnostic
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
        if observed is not None and key in identities:
            observed["identity_evidence"] = identities[key].evidence_id
        if observed is not None and key in groupings:
            observed["grouping_evidence"] = groupings[key].evidence_id
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


def synchronize(engine, batches, *, checked_at=None, provider=None, synthetic=True):
    """Own all transactions. No caller Session is accepted or implicitly committed.

    This V1 development entry point deliberately permits only explicit local databases.
    Audit cannot be guaranteed if PostgreSQL itself is unavailable; errors propagate.
    """
    if engine.url.host not in {"127.0.0.1", "localhost", "::1"}:
        _error("local_database_required")
    now = checked_at or datetime.now(timezone.utc)
    if now.tzinfo is None or type(now.date()) is not date:
        _error("invalid_timestamp")
    batches = tuple(batches)
    conflicts, signatures = set(), {}
    for batch in batches:
        for observation in batch.details:
            signature = fingerprint(observation_facts(observation))
            if observation.key in signatures and signatures[observation.key] != signature:
                conflicts.add(observation.key)
            signatures[observation.key] = signature
    with engine.connect() as connection:
        locked = connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_KEY})
        connection.commit()
        if not locked:
            _error("import_busy")
        try:
            with Session(connection) as session:
                run = ImportRun(
                    started_at=now,
                    status="running",
                    parser_version=NORMALIZATION_VERSION,
                    synthetic=synthetic,
                    missing_marked=0,
                )
                session.add(run)
                session.commit()
                run_id, statuses, present = run.id, [], set()
                for batch in batches:
                    status, seen = _import_window(session, batch, run_id, now, provider, conflicts)
                    statuses.append(status)
                    present.update(seen)
                    session.commit()
                run = session.get(ImportRun, run_id)
                success = bool(statuses) and all(status == "success" for status in statuses)
                if success:
                    for race in session.scalars(
                        select(Race).join(SourceRecord).where(SourceRecord.provider == "ffc")
                    ):
                        if race.id in present or race.source.checked_at > now:
                            continue
                        covered = any(
                            race.department == batch.calendar.effective_department
                            and race.start_date <= batch.calendar.effective_end
                            and race.end_date >= batch.calendar.effective_start
                            for batch in batches
                        )
                        if covered and race.source_presence != "to_verify":
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
