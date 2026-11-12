"""Private persistence foundation, not authentication or an HTTP interface.

The caller owns its transaction. A future server authentication layer must obtain
the Account in this same Session; no request-provided actor ID is accepted here.
"""

from sqlalchemy import delete, func, inspect, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import object_session, selectinload

from raceatlas.models import Account, SavedEntry, opaque_id

SAVED_STATUSES = frozenset({"interested", "planned", "registered", "completed"})


class PlanningError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class PlanningNotFound(PlanningError):
    def __init__(self):
        super().__init__("not_found", "Saved entry not found.")


def normalize_email(value):
    """Account policy: trim and lowercase; preserve dots and plus tags.

    This is minimal shape validation, not full RFC validation, mailbox ownership,
    Unicode/IDNA canonicalization or a deliverability check.
    """
    if not isinstance(value, str):
        raise PlanningError("invalid_email", "Invalid email address.")
    normalized = value.strip().lower()
    if (
        len(normalized) > 254
        or normalized.count("@") != 1
        or not all(normalized.split("@"))
        or any(character.isspace() or not character.isprintable() for character in normalized)
    ):
        raise PlanningError("invalid_email", "Invalid email address.")
    return normalized


def create_account(session, email):
    """Create an unauthenticated private identity; the caller supplies credentials later."""
    statement = (
        insert(Account)
        .values(id=opaque_id(), email_normalized=normalize_email(email))
        .on_conflict_do_nothing(index_elements=[Account.email_normalized])
        .returning(Account)
    )
    account = session.scalars(statement).one_or_none()
    if account is None:
        raise PlanningError("account_unavailable", "Account unavailable.")
    return account


def _actor_id(session, actor):
    if (
        not isinstance(actor, Account)
        or object_session(actor) is not session
        or not inspect(actor).persistent
    ):
        raise PlanningNotFound()
    return actor.id


def _status(value):
    if not isinstance(value, str) or value not in SAVED_STATUSES:
        raise PlanningError("invalid_status", "Invalid saved status.")
    return value


def _target_id(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 64:
        raise PlanningNotFound()
    return value


def get_saved_entry(session, actor, entry_id):
    entry = session.scalar(
        select(SavedEntry)
        .where(
            SavedEntry.account_id == _actor_id(session, actor),
            SavedEntry.id == _target_id(entry_id),
        )
        .options(selectinload(SavedEntry.scope))
        .execution_options(populate_existing=True)
    )
    if entry is None:
        raise PlanningNotFound()
    return entry


def list_saved_entries(session, actor):
    return list(
        session.scalars(
            select(SavedEntry)
            .where(SavedEntry.account_id == _actor_id(session, actor))
            .options(selectinload(SavedEntry.scope))
            .order_by(SavedEntry.created_at, SavedEntry.id)
            .execution_options(populate_existing=True)
        )
    )


def put_saved_entry(session, actor, scope_id, status="interested"):
    account_id = _actor_id(session, actor)
    statement = insert(SavedEntry).values(
        id=opaque_id(), account_id=account_id, scope_id=_target_id(scope_id), status=_status(status)
    )
    statement = statement.on_conflict_do_update(
        index_elements=[SavedEntry.account_id, SavedEntry.scope_id],
        set_={
            "status": statement.excluded.status,
            "updated_at": func.clock_timestamp(),
            "revision": SavedEntry.revision + 1,
        },
        where=SavedEntry.status != statement.excluded.status,
    ).returning(SavedEntry)
    try:
        with session.begin_nested():
            entry = session.scalars(
                statement, execution_options={"populate_existing": True}
            ).one_or_none()
    except IntegrityError as error:
        if getattr(error.orig, "sqlstate", None) == "23503":
            raise PlanningNotFound() from None
        raise
    if entry is None:
        # A no-op conflict returns no row. Read without issuing a physical UPDATE.
        entry = session.scalar(
            select(SavedEntry)
            .where(SavedEntry.account_id == account_id, SavedEntry.scope_id == scope_id)
            .execution_options(populate_existing=True)
        )
        if entry is None:
            raise PlanningNotFound()
    return entry


def update_saved_entry(session, actor, entry_id, status):
    account_id = _actor_id(session, actor)
    # Check ownership before validating input: a foreign entry always stays not_found.
    get_saved_entry(session, actor, entry_id)
    value = _status(status)
    session.execute(
        update(SavedEntry)
        .where(
            SavedEntry.account_id == account_id,
            SavedEntry.id == entry_id,
            SavedEntry.status != value,
        )
        .values(status=value, updated_at=func.clock_timestamp(), revision=SavedEntry.revision + 1)
        .execution_options(synchronize_session=False)
    )
    return get_saved_entry(session, actor, entry_id)


def delete_saved_entry(session, actor, entry_id):
    deleted = session.scalar(
        delete(SavedEntry)
        .where(
            SavedEntry.account_id == _actor_id(session, actor),
            SavedEntry.id == _target_id(entry_id),
        )
        .returning(SavedEntry.id)
    )
    if deleted is None:
        raise PlanningNotFound()


def delete_account(session, actor):
    """Delete only this identity and its private rows; no source graph is changed."""
    account_id = _actor_id(session, actor)
    session.execute(delete(Account).where(Account.id == account_id))
