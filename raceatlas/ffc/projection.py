"""Build detached ORM graphs; caller owns transactions and source reconciliation.

No session, automatic lookup, deletion or update is performed here. Reusing identities
requires a complete externally reviewed attestation, not similarity or display rank.
"""

from dataclasses import asdict, dataclass
from uuid import uuid4

from raceatlas.models import EligibilityRule, EntryScope, Race, RaceType, RuleCategory, SourceRecord

from .types import AdapterError, SourceKey


@dataclass(frozen=True)
class IdentityAttestation:
    key: SourceKey
    race_id: str
    evidence_id: str
    # Observation-local random token -> attested existing internal identifier.
    scope_ids: tuple[tuple[str, str], ...]
    rule_ids: tuple[tuple[str, str], ...]


def _binding(pairs, tokens, expected, field):
    mapping = dict(pairs)
    if (
        len(mapping) != len(pairs)
        or set(mapping) != set(tokens)
        or len(set(mapping.values())) != len(mapping)
        or set(mapping.values()) != set(expected)
    ):
        raise AdapterError(
            "identity_needs_review", field, "Complete bijective attestation required"
        )
    return mapping


def project_race(observation, *, existing=None, attestation=None):
    """Project a parse result. Never attach the returned graph alongside an existing one.

    For revisions, the integration layer must reconcile the detached result explicitly in
    one transaction. Projection intentionally refuses missing/extra identities until reviewed.
    """
    scope_ids, rule_ids = {}, {}
    if existing is not None:
        key = SourceKey(existing.source.source_season, existing.source.race_number)
        if existing.source.provider != "ffc" or key != observation.key:
            raise AdapterError("identity_needs_review", "source", "Source alias requires review")
        if existing.source.checked_at.tzinfo is None:
            raise AdapterError(
                "invalid_timestamp", "existing", "Timezone-aware source time required"
            )
        if observation.checked_at < existing.source.checked_at:
            raise AdapterError(
                "stale_observation", "checked_at", "Older observation cannot revise facts"
            )
        if (
            attestation is None
            or not attestation.evidence_id.strip()
            or attestation.key != key
            or attestation.race_id != existing.id
        ):
            raise AdapterError("identity_needs_review", "race", "Explicit identity review required")
        scope_ids = _binding(
            attestation.scope_ids,
            [scope.token for scope in observation.scopes],
            [scope.id for scope in existing.scopes],
            "scopes",
        )
        rule_ids = _binding(
            attestation.rule_ids,
            [rule.token for scope in observation.scopes for rule in scope.rules],
            [rule.id for scope in existing.scopes for rule in scope.rules],
            "rules",
        )
        previous = {scope.id: {rule.id for rule in scope.rules} for scope in existing.scopes}
        for scope in observation.scopes:
            if {rule_ids[rule.token] for rule in scope.rules} != previous[scope_ids[scope.token]]:
                raise AdapterError(
                    "identity_needs_review", "rules", "Rules cannot move across scopes"
                )
        # An attestation proves identity, not that a failed/partial parse can erase history.
        if (
            observation.diagnostics
            or existing.organizer is not None
            and observation.organizer is None
            or existing.types
            and not observation.types
            or existing.status != "unknown"
            and observation.status == "unknown"
            and existing.status != "cancelled"
        ):
            raise AdapterError(
                "incomplete_revision", "race", "Partial revision requires reconciliation"
            )
        old_rules = {rule.id: rule for scope in existing.scopes for rule in scope.rules}
        for scope in observation.scopes:
            for rule in scope.rules:
                previous_rule = old_rules[rule_ids[rule.token]]
                for field, value in asdict(rule.restrictions).items():
                    old_value = getattr(previous_rule, field)
                    if old_value not in (None, "unknown", [], ()) and value in (
                        None,
                        "unknown",
                        [],
                        (),
                    ):
                        raise AdapterError(
                            "incomplete_revision", field, "Unknown restriction cannot erase history"
                        )
        if existing.commune_id and existing.department != observation.department:
            raise AdapterError(
                "identity_needs_review", "commune", "Existing location contradicts source"
            )
    elif attestation is not None:
        raise AdapterError("identity_needs_review", "race", "Attestation requires existing graph")
    race = Race(
        id=existing.id if existing else str(uuid4()),
        competition_id=existing.competition_id if existing else None,
        commune_id=existing.commune_id if existing else None,
        name=observation.name,
        discipline=observation.discipline,
        organizer=observation.organizer,
        start_date=observation.start_date,
        end_date=observation.end_date,
        department=observation.department,
        status=(
            "cancelled"
            if existing and existing.status == "cancelled" and observation.status == "unknown"
            else observation.status
        ),
        source_presence="present",
        revision=existing.revision + 1 if existing else 1,
    )
    race.source = SourceRecord(
        provider="ffc",
        source_season=observation.key.season,
        race_number=observation.key.race_number,
        source_url=observation.source_url,
        checked_at=observation.checked_at,
    )
    race.types = [
        RaceType(code=code, discipline=observation.discipline) for code in observation.types
    ]
    for position, item in enumerate(observation.scopes):
        previous_scope = (
            next(scope for scope in existing.scopes if scope.id == scope_ids[item.token])
            if existing
            else None
        )
        scope = EntryScope(
            id=scope_ids.get(item.token, str(uuid4())),
            position=position,
            kind=item.kind,
            raw_label=item.raw_label,
            source_list_id=previous_scope.source_list_id if previous_scope else None,
            identity_status=previous_scope.identity_status if previous_scope else "unverified",
            eligibility_status=item.eligibility_status,
        )
        for index, definition in enumerate(item.rules):
            restrictions = asdict(definition.restrictions)
            restrictions["engagers"] = list(restrictions["engagers"])
            rule = EligibilityRule(
                id=rule_ids.get(definition.token, str(uuid4())),
                position=index,
                raw_label=definition.raw_label,
                evidence_id=definition.evidence_id,
                normalization_version=observation.normalization_version,
                **restrictions,
            )
            rule.categories = [
                RuleCategory(category_code=code, position=i)
                for i, code in enumerate(definition.category_codes)
            ]
            scope.rules.append(rule)
        race.scopes.append(scope)
    return race
