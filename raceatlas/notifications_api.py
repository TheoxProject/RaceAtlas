"""Exact virtual private notifications; caller owns commit/rollback and timeouts."""

import base64
import binascii
import hashlib
import hmac
import json
import re
from datetime import datetime

from sqlalchemy import and_, func, literal, select, true, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload, raiseload

from raceatlas.changes import transaction_connection
from raceatlas.models import (
    EligibilityRule,
    EntryScope,
    PersonalNotification,
    Race,
    RaceChange,
    SavedEntry,
    ScopeChange,
)
from raceatlas.planning import _actor_id, _lock_actor, _target_id
from raceatlas.planning_snapshot import PlanningLimits, _document, encode_personal
from raceatlas.serialization import timestamp


class NotificationQueryError(ValueError):
    def __init__(self):
        super().__init__("Invalid notification query.")


def _b64(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def parse_query(limit=50, cursor=None):
    """All syntax/size checks are pure, before any admission/auth/private SQL."""
    if isinstance(limit, str) and len(limit) <= 3 and limit.isascii() and limit.isdecimal():
        limit = int(limit)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise NotificationQueryError()
    if cursor is None:
        return limit, None
    if (
        not isinstance(cursor, str)
        or not 1 <= len(cursor) <= 1024
        or not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}", cursor)
    ):
        raise NotificationQueryError()
    body, signature = cursor.split(".")
    try:
        raw = base64.b64decode(body + "=" * (-len(body) % 4), altchars=b"-_", validate=True)
        if raw.startswith(b"2\0"):
            parts = raw.split(b"\0")
            if len(parts) != 4:
                raise ValueError()
            date, change, scope = (part.decode("utf-8") for part in parts[1:])
        else:
            # Previously issued v1 cursors remain usable within the existing
            # 1024-character input bound; only new cursors use the compact codec.
            value = json.loads(raw.decode("utf-8"))
            if (
                not isinstance(value, list)
                or len(value) != 4
                or type(value[0]) is not int
                or value[0] != 1
            ):
                raise ValueError()
            date, change, scope = value[1:]
        at = datetime.fromisoformat(date)
        if at.tzinfo is None or timestamp(at) != date:
            raise ValueError()
        change_id, scope_id = _target_id(change), _target_id(scope)
        if _b64(raw) != body:
            raise ValueError()
    except (ValueError, TypeError, UnicodeError, binascii.Error, OverflowError):
        raise NotificationQueryError() from None
    return limit, (at, change_id, scope_id, body, signature)


def _mac(key, account_id, body):
    if not isinstance(key, bytes) or len(key) < 32:
        raise NotificationQueryError()
    message = (
        b"notifications-cursor:v1\x00" + account_id.encode("utf-8") + b"\x00" + body.encode("ascii")
    )
    return _b64(hmac.new(key, message, hashlib.sha256).digest())


def _cursor(key, account_id, at, change_id, scope_id):
    # NUL is already forbidden in opaque IDs. UTF-8 uses at most four bytes per
    # valid codepoint, including controls without JSON's six-byte escaping:
    # 2 + 27 + 1 + 256 + 1 + 256 = 543 raw bytes, 768 signed characters maximum.
    raw = b"2\0" + timestamp(at).encode("ascii") + b"\0"
    raw += _target_id(change_id).encode("utf-8") + b"\0" + _target_id(scope_id).encode("utf-8")
    body = _b64(raw)
    return body + "." + _mac(key, account_id, body)


def _eligible(account_id):
    return (
        select(
            SavedEntry.id.label("saved_id"),
            ScopeChange.change_id,
            ScopeChange.scope_id,
            RaceChange.created_at,
            PersonalNotification.read_at,
        )
        .select_from(SavedEntry)
        .join(ScopeChange, ScopeChange.scope_id == SavedEntry.scope_id)
        .join(RaceChange, RaceChange.id == ScopeChange.change_id)
        .outerjoin(
            PersonalNotification,
            and_(
                PersonalNotification.account_id == account_id,
                PersonalNotification.change_id == ScopeChange.change_id,
                PersonalNotification.scope_id == ScopeChange.scope_id,
            ),
        )
        .where(
            SavedEntry.account_id == account_id,
            ScopeChange.sequence > SavedEntry.notifications_after_sequence,
        )
    )


def read_notifications(session, actor, *, cursor_key, limit=50, cursor=None, limits=None):
    limit, claim = parse_query(limit, cursor)
    account_id = _actor_id(session, actor)
    # Even a first page validates configuration, without waiting for cursor creation.
    signature = _mac(cursor_key, account_id, claim[3] if claim else "")
    if claim and not hmac.compare_digest(signature, claim[4]):
        raise NotificationQueryError()
    transaction_connection(session)
    _lock_actor(session, actor)
    limits = PlanningLimits() if limits is None else limits
    eligible = _eligible(account_id).cte("eligible_notifications").prefix_with("MATERIALIZED")
    count = select(func.count().filter(eligible.c.read_at.is_(None)).label("unread_count")).cte(
        "notification_count"
    )
    page = select(eligible)
    if claim:
        page = page.where(
            tuple_(eligible.c.created_at, eligible.c.change_id, eligible.c.scope_id)
            < tuple_(*claim[:3])
        )
    page = (
        page.order_by(
            eligible.c.created_at.desc(), eligible.c.change_id.desc(), eligible.c.scope_id.desc()
        )
        .limit(limit + 1)
        .cte("notification_page")
    )
    statement = (
        select(
            count.c.unread_count,
            page,
            RaceChange.kind,
            RaceChange.provenance,
            ScopeChange.payload,
            SavedEntry,
            Race,
        )
        .select_from(count.outerjoin(page, true()))
        .outerjoin(SavedEntry, SavedEntry.id == page.c.saved_id)
        .outerjoin(EntryScope, EntryScope.id == SavedEntry.scope_id)
        .outerjoin(Race, Race.id == EntryScope.race_id)
        .outerjoin(RaceChange, RaceChange.id == page.c.change_id)
        .outerjoin(
            ScopeChange,
            and_(
                ScopeChange.change_id == page.c.change_id, ScopeChange.scope_id == page.c.scope_id
            ),
        )
        .options(
            raiseload("*"),
            joinedload(SavedEntry.scope)
            .joinedload(EntryScope.rules)
            .joinedload(EligibilityRule.categories),
            joinedload(Race.commune),
            joinedload(Race.types),
            joinedload(Race.source),
        )
        .order_by(page.c.created_at.desc(), page.c.change_id.desc(), page.c.scope_id.desc())
        .execution_options(populate_existing=True, notification_snapshot=True)
    )
    # Joined collections repeat a notification row. JSON facts are deliberately
    # unhashable: deduplicate on its immutable composite identity, not its payload.
    rows = session.execute(statement).unique(lambda row: (row.change_id, row.scope_id)).all()
    visible = [row for row in rows if row.change_id is not None]
    has_more = len(visible) > limit
    visible = visible[:limit]
    items = [
        dict(
            change_id=row.change_id,
            scope_id=row.scope_id,
            kind=row.kind,
            created_at=timestamp(row.created_at),
            read_at=timestamp(row.read_at),
            delta=row.payload,
            provenance=row.provenance,
            entry=_document(row.SavedEntry, row.Race),
        )
        for row in visible
    ]
    last = visible[-1] if has_more else None
    document = dict(
        items=items,
        unread_count=rows[0].unread_count,
        next_cursor=_cursor(cursor_key, account_id, last.created_at, last.change_id, last.scope_id)
        if last
        else None,
        has_more=has_more,
    )
    return encode_personal(document, limits)


def mark_all_notifications_read(session, actor):
    _actor_id(session, actor)
    transaction_connection(session)
    account_id = _lock_actor(session, actor)
    eligible = _eligible(account_id).cte("ack_eligible_notifications").prefix_with("MATERIALIZED")
    statement = insert(PersonalNotification).from_select(
        ["account_id", "change_id", "scope_id", "read_at"],
        select(
            literal(account_id),
            eligible.c.change_id,
            eligible.c.scope_id,
            func.statement_timestamp(),
        ).where(true()),
    )
    statement = statement.on_conflict_do_update(
        index_elements=[
            PersonalNotification.account_id,
            PersonalNotification.change_id,
            PersonalNotification.scope_id,
        ],
        set_={"read_at": statement.excluded.read_at},
        where=PersonalNotification.read_at.is_(None),
    ).execution_options(notification_ack=True)
    session.execute(statement)
