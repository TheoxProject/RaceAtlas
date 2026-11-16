"""Bounded account-owned projection. No stale candidate lists or background I/O."""

from dataclasses import dataclass

from sqlalchemy import and_, exists, literal, select
from sqlalchemy.dialects.postgresql import insert

from raceatlas.changes import transaction_connection
from raceatlas.models import PersonalNotification, RaceChange, SavedEntry, ScopeChange
from raceatlas.planning import _actor_id, _lock_actor


@dataclass(frozen=True)
class ProjectionResult:
    inserted: int
    pending: bool


def project_notifications(session, actor, *, batch_size=256):
    if type(batch_size) is not int or not 1 <= batch_size <= 1000:
        raise ValueError("Invalid projection batch")
    _actor_id(session, actor)
    transaction_connection(session)
    account_id = _lock_actor(session, actor)
    eligible = (
        select(literal(account_id), ScopeChange.change_id, ScopeChange.scope_id)
        .join(RaceChange, RaceChange.id == ScopeChange.change_id)
        .join(
            SavedEntry,
            and_(SavedEntry.scope_id == ScopeChange.scope_id, SavedEntry.account_id == account_id),
        )
        .outerjoin(
            PersonalNotification,
            and_(
                PersonalNotification.account_id == account_id,
                PersonalNotification.scope_id == ScopeChange.scope_id,
                PersonalNotification.change_id == ScopeChange.change_id,
            ),
        )
        .where(
            ScopeChange.sequence > SavedEntry.notifications_after_sequence,
            PersonalNotification.change_id.is_(None),
        )
        .order_by(RaceChange.created_at, ScopeChange.change_id, ScopeChange.scope_id)
    )
    statement = (
        insert(PersonalNotification)
        .from_select(["account_id", "change_id", "scope_id"], eligible.limit(batch_size))
        .on_conflict_do_nothing(
            index_elements=[
                PersonalNotification.account_id,
                PersonalNotification.change_id,
                PersonalNotification.scope_id,
            ]
        )
        .returning(PersonalNotification.change_id)
    )
    inserted = len(list(session.scalars(statement)))
    pending = session.scalar(select(exists(eligible.order_by(None))))
    return ProjectionResult(inserted, bool(pending))
