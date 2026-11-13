"""Private account proofs. Caller owns transaction; dispatch intents after commit only."""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import event, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from raceatlas.auth import _TOKEN, _lock_account, _now, _revoke_all
from raceatlas.auth.errors import AuthenticationFailed
from raceatlas.auth.passwords import hash_password, password_bytes
from raceatlas.email import EmailService
from raceatlas.email.config import mailbox
from raceatlas.models import (
    Account,
    AuthChallenge,
    AuthSession,
    EmailAddressQuota,
    EmailBudget,
    PasswordCredential,
    opaque_id,
)
from raceatlas.planning import normalize_email

from .flow_limits import FlowConfigurationError, FlowPolicy, admit


class InvalidProof(ValueError):
    def __init__(self):
        super().__init__("Invalid account proof.")


class EmailIntentUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("Email intent is not dispatchable.")


@dataclass(repr=False)
class EmailIntent:
    purpose: str
    recipient: str
    token: str
    account_id: str | None = field(default=None, repr=False, kw_only=True)
    operation_id: object = field(default_factory=uuid4)
    _status: str = field(default="pending", init=False)

    def dispatch_after_commit(self, email_service):
        if self._status != "committed" or not isinstance(email_service, EmailService):
            raise EmailIntentUnavailable()
        # A deliberate new request is recovery, never an implicit retry of secrets.
        self._status = "attempted"
        send = (
            email_service.send_confirmation
            if self.purpose == "confirmation"
            else email_service.send_password_reset
        )
        return send(self.recipient, self.token, operation_id=self.operation_id)


@dataclass(frozen=True)
class RequestResult:
    status: str = "accepted"
    intent: EmailIntent | None = field(default=None, repr=False)


def _after_commit(session):
    nested = session.get_nested_transaction()
    if nested is not None:
        session.info.setdefault("account_flow_committed_nested", set()).add(nested)
        return
    root = session.get_transaction()
    committed = session.info.get("account_flow_committed_nested", set())
    for intent, origin in session.info.pop("account_flow_intents", []):
        valid = True
        while origin.parent is not None:
            valid = valid and origin in committed
            origin = origin.parent
        intent._status = "committed" if valid and origin is root else "rolled_back"


def _after_rollback(session, previous_transaction):
    keep = []
    for intent, origin in session.info.get("account_flow_intents", []):
        node = origin
        while node is not None and node is not previous_transaction:
            node = node.parent
        if node is not None:
            intent._status = "rolled_back"
        else:
            keep.append((intent, origin))
    session.info["account_flow_intents"] = keep


def _after_transaction_end(session, transaction):
    if transaction.parent is None:
        for intent, _ in session.info.pop("account_flow_intents", []):
            intent._status = "rolled_back"
        session.info.pop("account_flow_committed_nested", None)
    elif transaction.nested and transaction not in session.info.get(
        "account_flow_committed_nested", set()
    ):
        _after_rollback(session, transaction)


class AccountFlowSession(Session):
    """Own one Engine's transactions; never join caller-owned Connections.

    Public bind-routing entry points are fenced, including Core statements and
    SessionTransaction.connection(). Server code that mutates SQLAlchemy/driver
    internals is outside this contract.
    """

    def __init__(self, bind, **kwargs):
        if (
            not isinstance(bind, Engine)
            or kwargs.get("binds") is not None
            or kwargs.get("twophase", False)
        ):
            raise FlowConfigurationError()
        self._flow_engine = bind
        super().__init__(bind=bind, **kwargs)

    def get_bind(self, mapper=None, *, clause=None, bind=None, **kwargs):
        resolved = super().get_bind(mapper, clause=clause, bind=bind, **kwargs)
        if resolved is not self._flow_engine:
            raise FlowConfigurationError()
        return resolved

    def connection(self, bind_arguments=None, execution_options=None):
        arguments = dict(bind_arguments) if bind_arguments is not None else None
        if arguments and arguments.get("bind", self._flow_engine) is not self._flow_engine:
            raise FlowConfigurationError()
        return super().connection(bind_arguments=arguments, execution_options=execution_options)

    def bind_mapper(self, mapper, bind):
        if bind is not self._flow_engine:
            raise FlowConfigurationError()
        return super().bind_mapper(mapper, bind)

    def bind_table(self, table, bind):
        if bind is not self._flow_engine:
            raise FlowConfigurationError()
        return super().bind_table(table, bind)


def _supported_session(session):
    # A Session bound to an external Connection can release a savepoint without
    # committing PostgreSQL. Refuse it before mutation rather than arm falsely.
    if not isinstance(session, AccountFlowSession):
        raise FlowConfigurationError()
    engine = session.get_bind(mapper=Account)
    if not isinstance(engine, Engine) or any(
        session.get_bind(mapper=model) is not engine
        for model in (
            PasswordCredential,
            AuthChallenge,
            AuthSession,
            EmailBudget,
            EmailAddressQuota,
        )
    ):
        raise FlowConfigurationError()
    # Even an Engine-bound Session must own a real transaction, not DBAPI autocommit.
    driver = session.connection().connection.driver_connection
    if getattr(driver, "autocommit", True) is not False:
        raise FlowConfigurationError()


def _track(session, intent):
    if not session.info.get("account_flow_hooks"):
        event.listen(session, "after_commit", _after_commit)
        event.listen(session, "after_soft_rollback", _after_rollback)
        event.listen(session, "after_transaction_end", _after_transaction_end)
        session.info["account_flow_hooks"] = True
    origin = session.get_nested_transaction() or session.get_transaction()
    session.info.setdefault("account_flow_intents", []).append((intent, origin))
    return RequestResult(intent=intent)


def _policy(policy):
    if policy is None:
        return FlowPolicy.from_environment()
    if not isinstance(policy, FlowPolicy):
        raise FlowConfigurationError()
    return policy


def _email(value):
    return mailbox(normalize_email(value))


def _credential(session, account_id):
    return session.scalar(
        select(PasswordCredential)
        .where(PasswordCredential.account_id == account_id)
        .execution_options(populate_existing=True)
    )


def _by_email(session, email, *, create=False):
    created = None
    if create:
        created = session.scalar(
            insert(Account)
            .values(
                id=opaque_id(),
                email_normalized=email,
            )
            .on_conflict_do_nothing(index_elements=[Account.email_normalized])
            .returning(Account.id)
        )
    account = session.scalar(
        select(Account)
        .where(Account.email_normalized == email)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if account is not None and account in session.deleted:
        account = None
    return account, created is not None


def _digest(purpose, token):
    if not isinstance(token, str) or not _TOKEN.fullmatch(token):
        raise InvalidProof()
    return hashlib.sha256(f"raceatlas:{purpose}:v1:{token}".encode("ascii")).hexdigest()


def _issue(session, account, credential, purpose, recipient):
    old = session.scalar(
        select(AuthChallenge)
        .where(
            AuthChallenge.account_id == account.id,
            AuthChallenge.purpose == purpose,
        )
        .execution_options(populate_existing=True)
    )
    if old is not None:
        session.delete(old)
        session.flush()
    now = _now(session)
    token = secrets.token_urlsafe(32)
    session.add(
        AuthChallenge(
            account_id=account.id,
            purpose=purpose,
            token_digest=_digest(purpose, token),
            credential_version=credential.session_version,
            created_at=now,
            expires_at=now + timedelta(hours=24)
            if purpose == "confirmation"
            else now + timedelta(minutes=30),
        )
    )
    session.flush()
    return _track(session, EmailIntent(purpose, recipient, token, account_id=account.id))


def request_registration(session, email, password, *, policy=None):
    _supported_session(session)
    policy, email = _policy(policy), _email(email)
    password_bytes(password)
    account, created = _by_email(session, email, create=True)
    credential = _credential(session, account.id) if account is not None else None
    eligible = account is not None and (credential is None or credential.email_verified_at is None)
    allowed = admit(session, email, "confirmation", policy, wants_send=eligible)
    if not eligible or not allowed:
        if created:
            session.delete(account)
            session.flush()
        return RequestResult()
    password_hash = hash_password(password)
    if credential is None:
        credential = PasswordCredential(
            account_id=account.id,
            password_hash=password_hash,
            email_verified_at=None,
            session_version=1,
        )
        session.add(credential)
    else:
        credential.password_hash = password_hash
        _revoke_all(session, credential)
    session.flush()
    return _issue(session, account, credential, "confirmation", email)


def _request_existing(session, email, purpose, policy):
    _supported_session(session)
    policy, email = _policy(policy), _email(email)
    account, _ = _by_email(session, email)
    credential = _credential(session, account.id) if account is not None else None
    now = _now(session)
    eligible = credential is not None and (
        credential.email_verified_at is None
        if purpose == "confirmation"
        else credential.email_verified_at is not None and credential.email_verified_at <= now
    )
    if not admit(session, email, purpose, policy, wants_send=eligible) or not eligible:
        return RequestResult()
    return _issue(session, account, credential, purpose, email)


def resend_confirmation(session, email, *, policy=None):
    return _request_existing(session, email, "confirmation", policy)


def request_password_reset(session, email, *, policy=None):
    return _request_existing(session, email, "reset", policy)


def _proof(session, token, purpose):
    _supported_session(session)
    digest = _digest(purpose, token)
    account_id = session.scalar(
        select(AuthChallenge.account_id).where(
            AuthChallenge.token_digest == digest,
            AuthChallenge.purpose == purpose,
        )
    )
    if account_id is None:
        raise InvalidProof()
    try:
        account = _lock_account(session, account_id)
    except AuthenticationFailed:
        raise InvalidProof() from None
    challenge = session.scalar(
        select(AuthChallenge)
        .where(
            AuthChallenge.token_digest == digest,
            AuthChallenge.purpose == purpose,
        )
        .execution_options(populate_existing=True)
    )
    credential = _credential(session, account.id)
    now = _now(session)
    if (
        challenge is None
        or credential is None
        or challenge.account_id != account.id
        or challenge.credential_version != credential.session_version
        or now >= challenge.expires_at
        or (purpose == "confirmation" and credential.email_verified_at is not None)
        or (
            purpose == "reset"
            and (credential.email_verified_at is None or credential.email_verified_at > now)
        )
    ):
        raise InvalidProof()
    return challenge, credential, now


def confirm_email(session, token):
    challenge, credential, now = _proof(session, token, "confirmation")
    credential.email_verified_at = now
    session.delete(challenge)
    session.flush()


def complete_password_reset(session, token, new_password):
    password_bytes(new_password)
    challenge, credential, _ = _proof(session, token, "reset")
    credential.password_hash = hash_password(new_password)
    _revoke_all(session, credential)
    session.delete(challenge)
    session.flush()


def email_intent_is_active(session, intent):
    """Read-only worker check. No Account lock, consumption, or outbound I/O."""
    _supported_session(session)
    if (
        not isinstance(intent, EmailIntent)
        or intent._status != "committed"
        or not isinstance(intent.purpose, str)
        or intent.purpose not in {"confirmation", "reset"}
        or not isinstance(intent.account_id, str)
        or not 1 <= len(intent.account_id) <= 64
        or any(not character.isprintable() for character in intent.account_id)
    ):
        return False
    try:
        digest = _digest(intent.purpose, intent.token)
    except InvalidProof:
        return False
    verified = (
        PasswordCredential.email_verified_at.is_(None)
        if intent.purpose == "confirmation"
        else PasswordCredential.email_verified_at <= func.clock_timestamp()
    )
    statement = (
        select(AuthChallenge.token_digest)
        .join(Account, Account.id == AuthChallenge.account_id)
        .join(PasswordCredential, PasswordCredential.account_id == Account.id)
        .where(
            AuthChallenge.token_digest == digest,
            AuthChallenge.account_id == intent.account_id,
            AuthChallenge.purpose == intent.purpose,
            AuthChallenge.expires_at > func.clock_timestamp(),
            AuthChallenge.credential_version == PasswordCredential.session_version,
            Account.email_normalized == intent.recipient,
            verified,
        )
    )
    return session.scalar(statement) is not None
