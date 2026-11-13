"""Internal credential/session service; caller owns commit/rollback.

All auth mutations lock Account first. Hold the lock through fresh verification,
issuance/revocation and commit; never publish a returned token before commit.
Future confirmation/reset must use this same lock order, not write around it.
"""

import hashlib
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select

from raceatlas.models import Account, AuthSession, PasswordCredential
from raceatlas.planning import PlanningError, normalize_email

from .errors import AuthenticationFailed, InvalidPassword, ReauthenticationFailed
from .passwords import dummy_verify, hash_password, password_bytes, verify_password

ABSOLUTE_LIFETIME = timedelta(days=7)
IDLE_LIFETIME = timedelta(hours=24)
_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}\Z", re.ASCII)


@dataclass(frozen=True)
class IssuedSession:
    token: str = field(repr=False)
    expires_at: datetime


def _digest(token):
    if not isinstance(token, str) or len(token) != 43 or not _TOKEN.fullmatch(token):
        raise AuthenticationFailed()
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _now(session):
    return session.scalar(select(func.clock_timestamp())).astimezone(timezone.utc)


def _lock_account(session, account_id):
    account = session.scalar(
        select(Account)
        .where(Account.id == account_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if account is None or account in session.deleted:
        raise AuthenticationFailed()
    return account


def _credential(session, account_id):
    credential = session.scalar(
        select(PasswordCredential)
        .where(
            PasswordCredential.account_id == account_id,
            PasswordCredential.email_verified_at <= func.clock_timestamp(),
        )
        .execution_options(populate_existing=True)
    )
    if credential is None or credential.email_verified_at is None:
        raise AuthenticationFailed()
    return credential


def authenticate(session, email, password):
    try:
        normalized = normalize_email(email)
        password_bytes(password)
    except (PlanningError, InvalidPassword):
        raise AuthenticationFailed() from None
    account_id = session.scalar(select(Account.id).where(Account.email_normalized == normalized))
    if account_id is None:
        dummy_verify(password)
        raise AuthenticationFailed()
    _lock_account(session, account_id)
    try:
        credential = _credential(session, account_id)
    except AuthenticationFailed:
        dummy_verify(password)
        raise
    if not verify_password(credential.password_hash, password):
        raise AuthenticationFailed()
    now = _now(session)
    token = secrets.token_urlsafe(32)
    session.add(
        AuthSession(
            token_digest=_digest(token),
            account_id=account_id,
            session_version=credential.session_version,
            created_at=now,
            last_seen_at=now,
            expires_at=now + ABSOLUTE_LIFETIME,
        )
    )
    session.flush()
    return IssuedSession(token, now + ABSOLUTE_LIFETIME)


def resolve_session(session, token):
    digest = _digest(token)
    account_id = session.scalar(
        select(AuthSession.account_id).where(AuthSession.token_digest == digest)
    )
    if account_id is None:
        raise AuthenticationFailed()
    account = _lock_account(session, account_id)
    credential = _credential(session, account_id)
    stored = session.scalar(
        select(AuthSession)
        .where(AuthSession.token_digest == digest)
        .execution_options(populate_existing=True)
    )
    now = _now(session)
    if (
        stored is None
        or stored.account_id != account.id
        or stored.session_version != credential.session_version
        or now >= stored.expires_at
        or now >= stored.last_seen_at + IDLE_LIFETIME
    ):
        raise AuthenticationFailed()
    stored.last_seen_at = max(stored.last_seen_at, now)
    session.flush()
    return account


def logout(session, token):
    account = resolve_session(session, token)
    session.execute(
        delete(AuthSession).where(
            AuthSession.token_digest == _digest(token), AuthSession.account_id == account.id
        )
    )


def _revoke_all(session, credential):
    credential.session_version += 1
    session.execute(delete(AuthSession).where(AuthSession.account_id == credential.account_id))
    session.flush()


def logout_all(session, token):
    account = resolve_session(session, token)
    _revoke_all(session, _credential(session, account.id))


def reauthenticate(session, token, current_password):
    """Verify current secret under Account lock without minting another session."""
    account = resolve_session(session, token)
    if not verify_password(_credential(session, account.id).password_hash, current_password):
        raise ReauthenticationFailed()
    return account


def change_password(session, token, current_password, new_password):
    account = reauthenticate(session, token, current_password)
    credential = _credential(session, account.id)
    credential.password_hash = hash_password(new_password)
    _revoke_all(session, credential)
