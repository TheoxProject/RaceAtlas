"""Transactional scoped facts. No synchronization, subscriber fanout or I/O here."""

import hashlib
import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from raceatlas.models import (
    Account,
    EntryScope,
    PersonalNotification,
    RaceChange,
    SavedEntry,
    ScopeChange,
    opaque_id,
)

FIELDS = frozenset(
    {
        "name",
        "start_date",
        "end_date",
        "status",
        "source_presence",
        "commune",
        "raw_label",
        "eligibility",
        "discipline",
        "types",
        "organizer",
        "competition",
    }
)


class ChangeError(ValueError):
    """Generic internal validation error; never include supplied fact contents."""


def _text(value, limit):
    if not isinstance(value, str) or not 1 <= len(value) <= limit or "\x00" in value:
        raise ChangeError("Invalid fact text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ChangeError("Invalid fact text") from None
    return value


def identifier(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 64 or "\x00" in value:
        raise ChangeError("Invalid identifier")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ChangeError("Invalid identifier") from None
    return value


def canonical(value):
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (ValueError, TypeError, UnicodeEncodeError, RecursionError):
        raise ChangeError("Invalid facts") from None


@dataclass
class ScopeGuard:
    session: object
    transaction: object
    scope_ids: tuple[str, ...]
    connection: object
    database_root: object
    database_nested: object
    active: bool = True

    def check(self, session, scope_ids):
        current = session.get_nested_transaction() or session.get_transaction()
        while current is not None and current is not self.transaction:
            current = current.parent
        if (
            not self.active
            or self.session is not session
            or not self.transaction.is_active
            or current is None
            or not set(scope_ids).issubset(self.scope_ids)
        ):
            raise ChangeError("Inactive or mismatched scope guard")
        if (
            not self.database_root.is_active
            or self.connection.closed
            or self.connection.get_transaction() is not self.database_root
            or self.database_nested is not None
            and not self.database_nested.is_active
        ):
            raise ChangeError("Inactive database scope guard")
        _single_bind(session)
        with session.no_autoflush:
            if session.connection() is not self.connection:
                raise ChangeError("Scope guard connection changed")


def _single_bind(session):
    binding = session.get_bind()
    if any(
        session.get_bind(mapper=model) is not binding
        for model in (
            Account,
            SavedEntry,
            EntryScope,
            RaceChange,
            ScopeChange,
            PersonalNotification,
        )
    ):
        raise ChangeError("Multiple or routed binds unsupported")


def transaction_connection(session):
    """The lock/baseline contract requires real READ COMMITTED transactions."""
    _single_bind(session)
    with session.no_autoflush:
        connection = session.connection()
        if (
            connection.connection.driver_connection.autocommit
            or connection.get_isolation_level() != "READ COMMITTED"
        ):
            raise ChangeError("READ COMMITTED transactional connection required")
    return connection


@contextmanager
def scope_guards(session, scope_ids):
    """Sorted transaction locks. Acquire before caller DML; never release early.

    The token tracks the actual SAVEPOINT when nested, not just the outer root.
    Rolling back that SAVEPOINT invalidates its token even if the root survives.
    """
    ids = tuple(sorted({identifier(value) for value in scope_ids}))
    if not ids or len(ids) > 1000:
        raise ChangeError("Invalid scope batch")
    connection = transaction_connection(session)
    with session.no_autoflush:
        for scope_id in ids:
            digest = hashlib.sha256(
                b"raceatlas:scope-change:v1:" + scope_id.encode("utf-8")
            ).digest()
            key = int.from_bytes(digest[:8], "big", signed=True)
            session.execute(select(func.pg_advisory_xact_lock(key)))
    guard = ScopeGuard(
        session,
        session.get_nested_transaction() or session.get_transaction(),
        ids,
        connection,
        connection.get_transaction(),
        connection.get_nested_transaction(),
    )
    try:
        yield guard
    finally:
        guard.active = False


def subscription_baseline(session, guard, scope_id):
    guard.check(session, [scope_id])
    return session.scalar(
        select(func.coalesce(func.max(ScopeChange.sequence), 0)).where(
            ScopeChange.scope_id == scope_id
        )
    )


def record_change(session, guard, *, race_id, event_key, kind, targets, provenance):
    """Caller-owned mutation key, scoped before/after facts, no implicit commit.

    Keys identify mutation incarnations, NOT just business hashes (A→B→A→B).
    The future sync caller must acquire guards before its writes/SAVEPOINT.
    """
    identifier(race_id)
    _text(event_key, 128)
    if kind not in {"business", "presence"}:
        raise ChangeError("Invalid change identity")
    if not isinstance(targets, dict) or len(targets) > 1000:
        raise ChangeError("Invalid scope batch")
    clean = {}
    for scope_id, delta in targets.items():
        identifier(scope_id)
        if not isinstance(delta, dict) or set(delta) != {"before", "after"}:
            raise ChangeError("Invalid delta")
        before, after = delta["before"], delta["after"]
        if (
            not isinstance(before, dict)
            or not isinstance(after, dict)
            or set(before) != set(after)
            or not set(before).issubset(FIELDS)
        ):
            raise ChangeError("Invalid delta fields")
        changed = sorted(key for key in before if before[key] != after[key])
        if changed:
            payload = {
                "before": {key: before[key] for key in changed},
                "after": {key: after[key] for key in changed},
            }
            if len(canonical(payload)) > 16 * 1024:
                raise ChangeError("Delta too large")
            clean[scope_id] = payload
    if not clean:
        return None
    guard.check(session, clean)
    if (
        not isinstance(provenance, dict)
        or set(provenance) - {"source_url", "checked_at", "normalization_version", "evidence_id"}
        or not {"source_url", "checked_at", "normalization_version"}.issubset(provenance)
        or len(canonical(provenance)) > 4096
    ):
        raise ChangeError("Invalid provenance")
    provenance = dict(provenance)
    try:
        url = urlsplit(_text(provenance["source_url"], 2048))
        checked_at = datetime.fromisoformat(_text(provenance["checked_at"], 64))
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or checked_at.tzinfo is None
            or checked_at.utcoffset() is None
        ):
            raise ChangeError("Invalid provenance")
        provenance["checked_at"] = checked_at.astimezone(timezone.utc).isoformat()
        _text(provenance["normalization_version"], 64)
        if "evidence_id" in provenance:
            _text(provenance["evidence_id"], 128)
    except (ValueError, TypeError):
        raise ChangeError("Invalid provenance") from None
    signature = hashlib.sha256(
        canonical({"kind": kind, "targets": clean, "provenance": provenance})
    ).hexdigest()
    session.flush()
    scopes = set(
        session.scalars(
            select(EntryScope.id).where(EntryScope.race_id == race_id, EntryScope.id.in_(clean))
        )
    )
    if scopes != set(clean):
        raise ChangeError("Invalid scope target")
    existing = session.scalar(
        select(RaceChange).where(RaceChange.race_id == race_id, RaceChange.event_key == event_key)
    )
    if existing:
        if existing.signature != signature:
            raise ChangeError("Mutation key conflict")
        return existing.id
    sequences = dict(
        session.execute(
            select(ScopeChange.scope_id, func.max(ScopeChange.sequence))
            .where(ScopeChange.scope_id.in_(clean))
            .group_by(ScopeChange.scope_id)
        ).all()
    )
    if any(value >= 9223372036854775807 for value in sequences.values()):
        raise ChangeError("Sequence exhausted")
    change_id = opaque_id()
    statement = (
        insert(RaceChange)
        .values(
            id=change_id,
            race_id=race_id,
            event_key=event_key,
            kind=kind,
            signature=signature,
            provenance=provenance,
        )
        .on_conflict_do_nothing(index_elements=[RaceChange.race_id, RaceChange.event_key])
        .returning(RaceChange.id)
    )
    inserted = session.scalar(statement)
    if inserted is None:
        existing = session.scalar(
            select(RaceChange).where(
                RaceChange.race_id == race_id, RaceChange.event_key == event_key
            )
        )
        if existing.signature != signature:
            raise ChangeError("Mutation key conflict")
        return existing.id
    session.execute(
        insert(ScopeChange),
        [
            {
                "change_id": change_id,
                "scope_id": scope_id,
                "sequence": sequences.get(scope_id, 0) + 1,
                "payload": payload,
            }
            for scope_id, payload in sorted(clean.items())
        ],
    )
    return change_id
