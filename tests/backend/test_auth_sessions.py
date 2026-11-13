import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from queue import Queue
from threading import Event, current_thread

import pytest
from sqlalchemy import event, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, object_session

import raceatlas.auth as auth
from raceatlas.auth.errors import AuthenticationFailed, InvalidPassword
from raceatlas.auth.passwords import hash_password, verify_password
from raceatlas.models import (
    Account,
    AuthSession,
    CatalogState,
    PasswordCredential,
    Race,
    SavedEntry,
)
from raceatlas.planning import (
    PlanningNotFound,
    create_account,
    delete_account,
    get_saved_entry,
    put_saved_entry,
)

PASSWORD = " Synthetic Exact Passphrase 25 "
NEW_PASSWORD = " Replacement Exact Passphrase 26 "
T0 = datetime(2027, 1, 1, 12, tzinfo=timezone.utc)


def identity(session, email="auth@example.test", *, verified=True, credentials=True):
    account = create_account(session, email)
    if credentials:
        session.add(
            PasswordCredential(
                account_id=account.id,
                password_hash=hash_password(PASSWORD),
                email_verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc) if verified else None,
            )
        )
        session.flush()
    return account


def denied(call):
    with pytest.raises(AuthenticationFailed, match="^Authentication failed\\.$"):
        call()


@pytest.mark.parametrize("zone", ["UTC", "Europe/Paris", "Pacific/Honolulu"])
def test_sessions_are_independent_hashed_persistent_and_return_utc(session, database, zone):
    session.execute(select(func.set_config("TimeZone", zone, True)))
    account = identity(session)
    first = auth.authenticate(session, " AUTH@example.test ", PASSWORD)
    second = auth.authenticate(session, account.email_normalized, PASSWORD)
    assert len(first.token) == 43 and first.token != second.token
    assert first.token not in repr(first)
    rows = session.scalars(select(AuthSession)).all()
    assert {row.token_digest for row in rows} == {
        hashlib.sha256(token.encode()).hexdigest() for token in [first.token, second.token]
    }
    for row in rows:
        assert row.expires_at - row.created_at == timedelta(days=7)
        assert (
            row.created_at.utcoffset()
            == row.last_seen_at.utcoffset()
            == row.expires_at.utcoffset()
            == timedelta(0)
        )
    account_id = account.id
    session.commit()
    with Session(database) as reopened:
        actor = auth.resolve_session(reopened, first.token)
        assert (
            actor.id == account_id
            and object_session(actor) is reopened
            and inspect(actor).persistent
        )
        reopened.commit()


@pytest.mark.parametrize(
    "kind",
    [
        "account_only",
        "unverified",
        "wrong_password",
        "unknown_email",
        "invalid_email",
        "invalid_password",
        "future_proof",
    ],
)
def test_only_verified_credentials_allow_login_with_generic_failure(session, kind):
    identity(session, verified=kind != "unverified", credentials=kind != "account_only")
    if kind == "future_proof":
        session.scalar(select(PasswordCredential)).email_verified_at = datetime.now(
            timezone.utc
        ) + timedelta(days=1)
    email = (
        "unknown@example.test"
        if kind == "unknown_email"
        else "bad"
        if kind == "invalid_email"
        else "auth@example.test"
    )
    password = (
        "wrong synthetic password"
        if kind == "wrong_password"
        else "short"
        if kind == "invalid_password"
        else PASSWORD
    )
    denied(lambda: auth.authenticate(session, email, password))
    assert session.is_active and session.scalar(select(func.count()).select_from(AuthSession)) == 0


@pytest.mark.parametrize(
    "token",
    [
        None,
        {},
        1,
        "",
        "a" * 42,
        "a" * 44,
        "a" * 10000,
        "a" * 42 + "\x00",
        "a" * 42 + "\ud800",
        "a" * 42 + "é",
        "a" * 42 + "\n",
    ],
)
def test_invalid_tokens_fail_before_storage_without_echoing(session, token):
    count = []

    def observed(*args):
        count.append(1)

    event.listen(session.bind, "before_cursor_execute", observed)
    try:
        for operation in [auth.resolve_session, auth.logout, auth.logout_all]:
            denied(lambda: operation(session, token))
    finally:
        event.remove(session.bind, "before_cursor_execute", observed)
    assert count == [] and session.scalar(select(1)) == 1


@pytest.mark.parametrize(
    "kind,delta,valid",
    [
        ("idle", timedelta(hours=24, microseconds=-1), True),
        ("idle", timedelta(hours=24), False),
        ("idle", timedelta(hours=24, microseconds=1), False),
        ("absolute", timedelta(days=7, microseconds=-1), True),
        ("absolute", timedelta(days=7), False),
        ("absolute", timedelta(days=7, microseconds=1), False),
    ],
)
def test_server_expiration_boundaries_and_no_resurrection(session, monkeypatch, kind, delta, valid):
    identity(session)
    monkeypatch.setattr(auth, "_now", lambda session: T0)
    grant = auth.authenticate(session, "auth@example.test", PASSWORD)
    row = session.scalar(select(AuthSession))
    if kind == "absolute":
        row.last_seen_at = T0 + timedelta(days=6, hours=23)
        session.flush()
    previous = row.last_seen_at
    monkeypatch.setattr(auth, "_now", lambda session: T0 + delta)
    if valid:
        auth.resolve_session(session, grant.token)
        assert row.last_seen_at == T0 + delta
    else:
        denied(lambda: auth.resolve_session(session, grant.token))
        assert row.last_seen_at == previous
        denied(lambda: auth.resolve_session(session, grant.token))
    assert row.expires_at == T0 + timedelta(days=7)


def test_idle_touch_never_extends_absolute_deadline(session, monkeypatch):
    identity(session)
    monkeypatch.setattr(auth, "_now", lambda session: T0)
    grant = auth.authenticate(session, "auth@example.test", PASSWORD)
    for hours in [12, 24, 36, 48, 60, 72, 84, 96, 108, 120, 132, 144, 156, 167]:
        monkeypatch.setattr(auth, "_now", lambda session, hours=hours: T0 + timedelta(hours=hours))
        auth.resolve_session(session, grant.token)
    monkeypatch.setattr(auth, "_now", lambda session: T0 + timedelta(days=7))
    denied(lambda: auth.resolve_session(session, grant.token))
    assert session.scalar(select(AuthSession)).expires_at == grant.expires_at


def test_logout_one_all_and_other_accounts_are_isolated(session):
    alice = identity(session)
    bob = identity(session, "other@example.test")
    a = auth.authenticate(session, alice.email_normalized, PASSWORD)
    sibling = auth.authenticate(session, alice.email_normalized, PASSWORD)
    other = auth.authenticate(session, bob.email_normalized, PASSWORD)
    auth.logout(session, a.token)
    denied(lambda: auth.resolve_session(session, a.token))
    assert auth.resolve_session(session, sibling.token).id == alice.id
    auth.logout_all(session, sibling.token)
    denied(lambda: auth.resolve_session(session, sibling.token))
    assert auth.resolve_session(session, other.token).id == bob.id
    assert session.get(PasswordCredential, alice.id).session_version == 2
    assert session.get(PasswordCredential, bob.id).session_version == 1
    # A genuinely fresh proof after logout-all is allowed with the unchanged password.
    auth.authenticate(session, alice.email_normalized, PASSWORD)


def test_password_change_requires_proof_revokes_all_and_preserves_other_planning(seeded):
    alice = identity(seeded)
    bob = identity(seeded, "other@example.test")
    scope_id = seeded.get(Race, "race-road-combined").scopes[0].id
    owned = put_saved_entry(seeded, alice, scope_id, "planned")
    other = put_saved_entry(seeded, bob, scope_id, "registered")
    first = auth.authenticate(seeded, alice.email_normalized, PASSWORD)
    sibling = auth.authenticate(seeded, alice.email_normalized, PASSWORD)
    denied(lambda: auth.change_password(seeded, first.token, "wrong current secret", NEW_PASSWORD))
    with pytest.raises(InvalidPassword):
        auth.change_password(seeded, first.token, PASSWORD, "short")
    assert verify_password(seeded.get(PasswordCredential, alice.id).password_hash, PASSWORD)
    auth.change_password(seeded, first.token, PASSWORD, NEW_PASSWORD)
    for token in [first.token, sibling.token]:
        denied(lambda: auth.resolve_session(seeded, token))
    denied(lambda: auth.authenticate(seeded, alice.email_normalized, PASSWORD))
    new = auth.authenticate(seeded, alice.email_normalized, NEW_PASSWORD)
    actor = auth.resolve_session(seeded, new.token)
    assert get_saved_entry(seeded, actor, owned.id).status == "planned"
    with pytest.raises(PlanningNotFound):
        get_saved_entry(seeded, actor, other.id)
    assert get_saved_entry(seeded, bob, other.id).status == "registered"


def test_caller_rollback_controls_issuance_and_revocation(session, database):
    identity(session)
    session.commit()
    uncommitted = auth.authenticate(session, "auth@example.test", PASSWORD)
    session.rollback()
    with Session(database) as reopened:
        denied(lambda: auth.resolve_session(reopened, uncommitted.token))
    committed = auth.authenticate(session, "auth@example.test", PASSWORD)
    session.commit()
    auth.change_password(session, committed.token, PASSWORD, NEW_PASSWORD)
    session.rollback()
    with Session(database) as reopened:
        auth.resolve_session(reopened, committed.token)
        auth.authenticate(reopened, "auth@example.test", PASSWORD)
        denied(lambda: auth.authenticate(reopened, "auth@example.test", NEW_PASSWORD))
        reopened.rollback()
    auth.logout_all(session, committed.token)
    session.rollback()
    auth.resolve_session(session, committed.token)


def test_preloaded_orm_cannot_reuse_old_password_session_or_expiry(session, database):
    account = identity(session)
    grant = auth.authenticate(session, account.email_normalized, PASSWORD)
    account_id = account.id
    session.commit()
    credential = session.get(PasswordCredential, account_id)
    cached = session.scalar(select(AuthSession))
    with Session(database) as other:
        auth.change_password(other, grant.token, PASSWORD, NEW_PASSWORD)
        other.commit()
    denied(lambda: auth.authenticate(session, "auth@example.test", PASSWORD))
    assert credential.session_version == 2 and not verify_password(
        credential.password_hash, PASSWORD
    )
    denied(lambda: auth.resolve_session(session, grant.token))
    fresh = auth.authenticate(session, "auth@example.test", NEW_PASSWORD)
    session.commit()
    cached = session.scalar(select(AuthSession))
    with Session(database) as other:
        row = other.get(AuthSession, cached.token_digest)
        row.last_seen_at = row.created_at
        row.created_at -= timedelta(days=8)
        row.last_seen_at = row.created_at
        row.expires_at = row.created_at + timedelta(days=7)
        other.commit()
    denied(lambda: auth.resolve_session(session, fresh.token))


def test_credential_deletion_cascades_sessions_without_resurrection(session):
    account = identity(session)
    grant = auth.authenticate(session, account.email_normalized, PASSWORD)
    session.delete(session.get(PasswordCredential, account.id))
    session.flush()
    session.add(
        PasswordCredential(
            account_id=account.id,
            password_hash=hash_password(PASSWORD),
            email_verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )
    session.flush()
    denied(lambda: auth.resolve_session(session, grant.token))
    auth.authenticate(session, account.email_normalized, PASSWORD)


def test_account_cascade_and_private_auth_writes_do_not_change_catalogue(seeded):
    baseline = seeded.scalar(select(CatalogState.revision))
    alice = identity(seeded)
    bob = identity(seeded, "other@example.test")
    scope = seeded.get(Race, "race-road-combined").scopes[0]
    put_saved_entry(seeded, alice, scope.id)
    other = put_saved_entry(seeded, bob, scope.id, "registered")
    first = auth.authenticate(seeded, alice.email_normalized, PASSWORD)
    second = auth.authenticate(seeded, bob.email_normalized, PASSWORD)
    actor = auth.resolve_session(seeded, first.token)
    delete_account(seeded, actor)
    seeded.flush()
    denied(lambda: auth.resolve_session(seeded, first.token))
    assert auth.resolve_session(seeded, second.token).id == bob.id
    assert seeded.scalar(select(func.count()).select_from(PasswordCredential)) == 1
    assert seeded.scalar(select(func.count()).select_from(SavedEntry)) == 1
    assert get_saved_entry(seeded, bob, other.id).status == "registered"
    assert seeded.scalar(select(CatalogState.revision)) == baseline


def test_database_credentials_unique_and_session_fk_checks(session):
    account = identity(session)
    grant = auth.authenticate(session, account.email_normalized, PASSWORD)
    digest = hashlib.sha256(grant.token.encode()).hexdigest()
    for sql in [
        "INSERT INTO password_credential SELECT * FROM password_credential",
        "UPDATE password_credential SET session_version=0",
        "UPDATE auth_session SET session_version=0",
        "UPDATE auth_session SET token_digest='not-a-hash'",
        "UPDATE auth_session SET expires_at=created_at",
    ]:
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.execute(text(sql))
    assert session.get(AuthSession, digest) is not None


@pytest.mark.parametrize(
    "mutation", ["logout_all", "change_password", "delete_account", "validate_vs_logout"]
)
def test_real_pg_serializes_old_proof_or_validation_against_revocation(
    session, database, monkeypatch, mutation
):
    account = identity(session)
    existing = auth.authenticate(session, account.email_normalized, PASSWORD)
    account_id = account.id
    session.commit()
    entered, release = Event(), Event()
    pid_queue = Queue()
    verify = auth.verify_password
    now = auth._now

    def paused_verify(*args):
        result = verify(*args)
        if current_thread().name == "old-auth-proof":
            assert result
            entered.set()
            assert release.wait(8)
        return result

    def paused_now(s):
        if current_thread().name == "old-auth-proof":
            entered.set()
            assert release.wait(8)
        return now(s)

    if mutation == "validate_vs_logout":
        monkeypatch.setattr(auth, "_now", paused_now)
    else:
        monkeypatch.setattr(auth, "verify_password", paused_verify)

    def old_proof():
        current_thread().name = "old-auth-proof"
        with Session(database) as s:
            s.execute(text("SET LOCAL statement_timeout='10s'"))
            if mutation == "validate_vs_logout":
                auth.resolve_session(s, existing.token)
                token = existing.token
            else:
                token = auth.authenticate(s, "auth@example.test", PASSWORD).token
            s.commit()
            return token

    def mutate():
        current_thread().name = "auth-revoker"
        with Session(database) as s:
            s.execute(text("SET LOCAL statement_timeout='10s'"))
            pid_queue.put(s.scalar(select(func.pg_backend_pid())))
            if mutation == "change_password":
                auth.change_password(s, existing.token, PASSWORD, NEW_PASSWORD)
            elif mutation == "delete_account":
                delete_account(s, s.get(Account, account_id))
            else:
                auth.logout_all(s, existing.token)
            s.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        old = pool.submit(old_proof)
        try:
            assert entered.wait(5)
            newer = pool.submit(mutate)
            pid = pid_queue.get(timeout=5)
            blocked = False
            deadline = time.monotonic() + 5
            with database.connect() as observer:
                while time.monotonic() < deadline:
                    if (
                        observer.scalar(
                            text("SELECT cardinality(pg_blocking_pids(:pid))"), {"pid": pid}
                        )
                        > 0
                    ):
                        blocked = True
                        break
                    time.sleep(0.01)
            assert blocked, "Second connection did not wait for the account lock"
        finally:
            release.set()
        token = old.result(timeout=15)
        newer.result(timeout=15)
    with Session(database) as check:
        denied(lambda: auth.resolve_session(check, token))
        if mutation == "delete_account":
            denied(lambda: auth.authenticate(check, "auth@example.test", PASSWORD))
        elif mutation == "change_password":
            denied(lambda: auth.authenticate(check, "auth@example.test", PASSWORD))
            auth.authenticate(check, "auth@example.test", NEW_PASSWORD)
        else:
            auth.authenticate(check, "auth@example.test", PASSWORD)
