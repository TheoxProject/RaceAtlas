import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from queue import Queue

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as RawSession

import raceatlas.auth as auth
import raceatlas.auth.flow_limits as limits
import raceatlas.auth.flows as flows
from raceatlas.auth.errors import AuthenticationFailed, InvalidPassword
from raceatlas.auth.flow_limits import FlowConfigurationError, FlowPolicy
from raceatlas.auth.flows import (
    AccountFlowSession,
    EmailIntentUnavailable,
    InvalidProof,
    complete_password_reset,
    confirm_email,
    request_password_reset,
    request_registration,
    resend_confirmation,
)
from raceatlas.auth.flows import (
    AccountFlowSession as Session,
)
from raceatlas.auth.passwords import verify_password
from raceatlas.email import EmailService
from raceatlas.email.config import EmailDeliveryError
from raceatlas.models import (
    Account,
    AuthChallenge,
    AuthSession,
    CatalogState,
    EmailAddressQuota,
    EmailBudget,
    PasswordCredential,
    Race,
    SavedEntry,
)
from raceatlas.planning import delete_account, put_saved_entry

PASSWORD = " Synthetic Original Passphrase 2026 "
NEW = " Replacement Exact Passphrase 2027 "
EMAIL = "person@example.test"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
KEY = b"synthetic-dedicated-rate-key-00000000"


@pytest.fixture
def session(database):
    with database.begin() as connection:
        connection.execute(delete(Account))
    with AccountFlowSession(database) as session:
        yield session
        session.rollback()


@pytest.fixture(autouse=True)
def isolated_quotas(database):
    with database.begin() as connection:
        connection.execute(delete(Account))
        connection.execute(delete(EmailAddressQuota))
        connection.execute(delete(EmailBudget))


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    now = [T0]
    monkeypatch.setattr(flows, "_now", lambda session: now[0])
    monkeypatch.setattr(limits, "_now", lambda session: now[0])
    return now


@pytest.fixture
def policy():
    return FlowPolicy(KEY, cooldown_seconds=0, per_hour=20)


def register(session, policy, email=EMAIL):
    return request_registration(session, email, PASSWORD, policy=policy).intent


def verified(session, policy, email=EMAIL):
    intent = register(session, policy, email)
    confirm_email(session, intent.token)
    return intent


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_pending_confirmed_hash_only_and_commit_before_simulated_dispatch(session, policy):
    intent = register(session, policy)
    account = session.scalar(select(Account))
    credential = session.get(PasswordCredential, account.id)
    challenge = session.scalar(select(AuthChallenge))
    assert credential.email_verified_at is None
    assert verify_password(credential.password_hash, PASSWORD)
    assert len(intent.token) == 43
    assert (
        challenge.token_digest
        == hashlib.sha256(f"raceatlas:confirmation:v1:{intent.token}".encode()).hexdigest()
    )
    assert challenge.expires_at - challenge.created_at == timedelta(hours=24)
    assert intent.token not in repr(intent) and EMAIL not in repr(intent)
    assert KEY.decode() not in repr(policy)
    service = EmailService.from_environment(
        {"RACEATLAS_ENV": "test", "APP_BASE_URL": "https://site.example.test"}
    )
    with pytest.raises(EmailIntentUnavailable):
        intent.dispatch_after_commit(service)
    with pytest.raises(AuthenticationFailed):
        auth.authenticate(session, EMAIL, PASSWORD)
    session.commit()
    assert intent.dispatch_after_commit(service).status == "simulated"
    with pytest.raises(EmailIntentUnavailable):
        intent.dispatch_after_commit(service)
    confirm_email(session, intent.token)
    assert credential.email_verified_at == T0
    assert count(session, AuthChallenge) == 0 and count(session, AuthSession) == 0
    with pytest.raises(InvalidProof):
        confirm_email(session, intent.token)
    auth.authenticate(session, EMAIL, PASSWORD)


def test_re_registration_replaces_hash_version_and_proof_but_resend_preserves_password(
    session, policy
):
    old = register(session, policy)
    credential = session.scalar(select(PasswordCredential))
    replacement = request_registration(session, EMAIL, NEW, policy=policy).intent
    assert credential.session_version == 2 and verify_password(credential.password_hash, NEW)
    with pytest.raises(InvalidProof):
        confirm_email(session, old.token)
    original_hash = credential.password_hash
    resend = resend_confirmation(session, EMAIL, policy=policy).intent
    assert original_hash == credential.password_hash and credential.session_version == 2
    with pytest.raises(InvalidProof):
        confirm_email(session, replacement.token)
    confirm_email(session, resend.token)
    assert auth.authenticate(session, EMAIL, NEW).token
    with pytest.raises(AuthenticationFailed):
        auth.authenticate(session, EMAIL, PASSWORD)


@pytest.mark.parametrize("future", [False, True])
def test_verified_or_future_verified_credentials_never_overwritten(session, policy, future):
    verified(session, policy)
    credential = session.scalar(select(PasswordCredential))
    if future:
        credential.email_verified_at = datetime(2099, 1, 1, tzinfo=timezone.utc)
    before = credential.password_hash, credential.session_version, credential.email_verified_at
    assert request_registration(session, EMAIL, NEW, policy=policy).intent is None
    assert resend_confirmation(session, EMAIL, policy=policy).intent is None
    assert before == (
        credential.password_hash,
        credential.session_version,
        credential.email_verified_at,
    )
    assert count(session, AuthChallenge) == 0


@pytest.mark.parametrize(
    "purpose,lifetime", [("confirmation", timedelta(hours=24)), ("reset", timedelta(minutes=30))]
)
@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_expiration_exact_boundary_and_server_time(
    session, policy, clock, purpose, lifetime, offset
):
    if purpose == "confirmation":
        intent = register(session, policy)

        def consume():
            return confirm_email(session, intent.token)
    else:
        verified(session, policy)
        intent = request_password_reset(session, EMAIL, policy=policy).intent

        def consume():
            return complete_password_reset(session, intent.token, NEW)

    row = session.scalar(select(AuthChallenge))
    assert row.expires_at - row.created_at == lifetime
    clock[0] = T0 + lifetime + timedelta(microseconds=offset)
    if offset < 0:
        consume()
    else:
        with pytest.raises(InvalidProof, match="^Invalid account proof\\.$"):
            consume()
        assert count(session, AuthChallenge) == 1


def test_reset_request_does_not_mutate_auth_then_reset_revokes_all_devices(session, policy):
    verified(session, policy)
    other = verified(session, policy, "other@example.test")
    first = auth.authenticate(session, EMAIL, PASSWORD)
    second = auth.authenticate(session, EMAIL, PASSWORD)
    other_session = auth.authenticate(session, other.recipient, PASSWORD)
    credential = session.scalar(
        select(PasswordCredential).join(Account).where(Account.email_normalized == EMAIL)
    )
    before = credential.password_hash, credential.session_version
    reset = request_password_reset(session, EMAIL, policy=policy).intent
    assert before == (credential.password_hash, credential.session_version)
    assert count(session, AuthSession) == 3
    with pytest.raises(InvalidProof):
        confirm_email(session, reset.token)
    with pytest.raises(InvalidPassword):
        complete_password_reset(session, reset.token, "short")
    assert count(session, AuthChallenge) == 1
    complete_password_reset(session, reset.token, NEW)
    for grant in [first, second]:
        with pytest.raises(AuthenticationFailed):
            auth.resolve_session(session, grant.token)
    assert auth.resolve_session(session, other_session.token)
    assert auth.authenticate(session, EMAIL, NEW)
    with pytest.raises(InvalidProof):
        complete_password_reset(session, reset.token, PASSWORD)


@pytest.mark.parametrize("action", ["logout_all", "change_password"])
def test_version_revocation_invalidates_old_reset_and_stale_orm(session, database, policy, action):
    verified(session, policy)
    grant = auth.authenticate(session, EMAIL, PASSWORD)
    reset = request_password_reset(session, EMAIL, policy=policy).intent
    session.commit()
    credential = session.scalar(select(PasswordCredential))
    session.scalar(select(AuthChallenge))
    with Session(database) as other:
        if action == "logout_all":
            auth.logout_all(other, grant.token)
        else:
            auth.change_password(other, grant.token, PASSWORD, NEW)
        other.commit()
    with pytest.raises(InvalidProof):
        complete_password_reset(session, reset.token, " Third Exact Passphrase 2028 ")
    assert credential.session_version == 2


@pytest.mark.parametrize(
    "token", [None, "", "A" * 42, "A" * 44, "A" * 42 + "\ud800", "A" * 42 + "\x00", {}, "A" * 43]
)
def test_invalid_tokens_are_generic_without_storage_growth(session, token):
    with pytest.raises(InvalidProof, match="^Invalid account proof\\.$"):
        confirm_email(session, token)
    assert count(session, AuthChallenge) == count(session, EmailAddressQuota) == 0


def test_rollback_and_savepoints_never_arm_email_intent(session, policy):
    service = EmailService.from_environment(
        {"APP_BASE_URL": "http://127.0.0.1:5000", "RACEATLAS_ENV": "test"}
    )
    rolled = register(session, policy)
    session.rollback()
    session.commit()
    with pytest.raises(EmailIntentUnavailable):
        rolled.dispatch_after_commit(service)
    assert count(session, Account) == 0
    with session.begin_nested():
        nested = register(session, policy)
    with pytest.raises(EmailIntentUnavailable):
        nested.dispatch_after_commit(service)
    session.commit()
    assert nested.dispatch_after_commit(service).status == "simulated"
    with pytest.raises(RuntimeError):
        with session.begin_nested():
            invalidated = register(session, policy, "rollback@example.test")
            raise RuntimeError("synthetic rollback")
    session.commit()
    with pytest.raises(EmailIntentUnavailable):
        invalidated.dispatch_after_commit(service)


def test_commit_failure_never_arms_intent_and_rollback_restores_proof(session, policy):
    intent = register(session, policy)
    session.add(Account(email_normalized=EMAIL))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    service = EmailService.from_environment(
        {"APP_BASE_URL": "https://site.example.test", "RACEATLAS_ENV": "test"}
    )
    with pytest.raises(EmailIntentUnavailable):
        intent.dispatch_after_commit(service)
    assert count(session, Account) == count(session, AuthChallenge) == 0


def test_provider_failure_after_commit_does_not_verify_account_or_return_budget(
    session, policy, monkeypatch
):
    intent = register(session, policy)
    session.commit()
    service = EmailService.from_environment(
        {"APP_BASE_URL": "https://site.example.test", "RACEATLAS_ENV": "test"}
    )

    def fail(*args, **kwargs):
        raise EmailDeliveryError()

    monkeypatch.setattr(service, "send_confirmation", fail)
    with pytest.raises(EmailDeliveryError):
        intent.dispatch_after_commit(service)
    assert session.scalar(select(PasswordCredential)).email_verified_at is None
    assert session.get(EmailBudget, 1).day_count == 1
    assert count(session, AuthChallenge) == 1


@pytest.mark.parametrize("email", ["é@example.test", "x@é.test", "x\x00@example.test", "bad"])
def test_unshippable_email_rejected_before_any_private_mutation(session, policy, email):
    with pytest.raises(ValueError):
        request_registration(session, email, PASSWORD, policy=policy)
    assert count(session, Account) == count(session, EmailBudget) == 0


@pytest.mark.parametrize("key", [b"", b"short", "not-bytes", b"x" * 1025])
def test_rate_secret_is_required_bounded_and_not_reflected(key):
    with pytest.raises(FlowConfigurationError, match="^Invalid account flow configuration\\.$"):
        FlowPolicy(key)
    with pytest.raises(FlowConfigurationError):
        FlowPolicy.from_environment({})


def test_private_flows_and_delete_preserve_other_account_saves_and_public_epoch(seeded, policy):
    baseline = seeded.scalar(select(CatalogState.revision))
    first = verified(seeded, policy)
    verified(seeded, policy, "other@example.test")
    accounts = seeded.scalars(select(Account).order_by(Account.email_normalized)).all()
    scope = seeded.get(Race, "race-road-combined").scopes[0]
    for account in accounts:
        put_saved_entry(seeded, account, scope.id, "planned")
    request_password_reset(seeded, first.recipient, policy=policy)
    chosen = next(a for a in accounts if a.email_normalized == EMAIL)
    delete_account(seeded, chosen)
    seeded.flush()
    assert count(seeded, Account) == count(seeded, SavedEntry) == 1
    assert count(seeded, AuthChallenge) == 0
    assert seeded.scalar(select(CatalogState.revision)) == baseline


def test_cooldown_hourly_limit_refusal_preserves_active_proof_and_last_admission(session, clock):
    policy = FlowPolicy(KEY)
    first = register(session, policy)
    quota = session.scalar(select(EmailAddressQuota))
    clock[0] = T0 + timedelta(seconds=59)
    assert resend_confirmation(session, EMAIL, policy=policy).intent is None
    assert quota.last_admitted_at == T0
    confirm_email(session, first.token)
    # Reset has its own purpose bucket; confirmation counts remain independent.
    first_reset = request_password_reset(session, EMAIL, policy=policy).intent
    for seconds in [60, 120]:
        clock[0] = T0 + timedelta(seconds=59 + seconds)
        current = request_password_reset(session, EMAIL, policy=policy).intent
        assert current is not None
    last_admission = clock[0]
    clock[0] += timedelta(seconds=60)
    assert request_password_reset(session, EMAIL, policy=policy).intent is None
    row = session.scalar(select(EmailAddressQuota).where(EmailAddressQuota.purpose == "reset"))
    assert row.last_admitted_at == last_admission and row.admitted == 3
    with pytest.raises(InvalidProof):
        complete_password_reset(session, first_reset.token, NEW)
    complete_password_reset(session, current.token, NEW)
    clock[0] = T0 + timedelta(hours=1, seconds=59)
    assert request_password_reset(session, EMAIL, policy=policy).intent is not None
    assert row.admitted == 3


def test_unknown_addresses_limited_and_pseudonymized_without_email_budget(session, policy):
    policy = replace(policy, per_hour=3)
    for _ in range(4):
        result = request_password_reset(session, "absent@example.test", policy=policy)
        assert result.status == "accepted" and result.intent is None
    quota = session.scalar(select(EmailAddressQuota))
    import hmac

    assert quota.address_digest == hmac.new(KEY, b"absent@example.test", hashlib.sha256).hexdigest()
    assert quota.admitted == 3 and quota.expires_at - quota.last_admitted_at == timedelta(hours=2)
    assert session.get(EmailBudget, 1).day_count == 0
    assert count(session, Account) == 0
    session.commit()
    assert session.scalar(select(EmailAddressQuota)).admitted == 3


def test_day_month_reservations_and_new_account_denial_are_durable(session, policy, clock):
    policy = replace(policy, per_day=1, per_month=2)
    first = register(session, policy)
    denied = register(session, policy, "denied@example.test")
    assert denied is None and count(session, Account) == 1
    session.commit()
    budget = session.get(EmailBudget, 1)
    assert (budget.day_count, budget.month_count) == (1, 1)
    clock[0] = T0 + timedelta(days=1)
    assert resend_confirmation(session, EMAIL, policy=policy).intent is not None
    clock[0] = T0 + timedelta(days=2)
    assert resend_confirmation(session, EMAIL, policy=policy).intent is None
    # A budget refusal must not delete a preexisting pending or its active proof.
    assert count(session, Account) == 1
    assert request_registration(session, EMAIL, NEW, policy=policy).intent is None
    assert verify_password(session.scalar(select(PasswordCredential)).password_hash, PASSWORD)
    assert budget.day_count == 0 and budget.month_count == 2
    clock[0] = datetime(2026, 2, 1, tzinfo=timezone.utc)
    assert resend_confirmation(session, EMAIL, policy=policy).intent is not None
    assert budget.day_count == budget.month_count == 1
    assert first.token not in repr(budget)


def test_ttl_cardinality_and_refused_new_account_preserve_existing_pending(session, policy, clock):
    policy = replace(policy, capacity=2)
    original = register(session, policy)
    request_password_reset(session, "unknown@example.test", policy=policy)
    assert register(session, policy, "overflow@example.test") is None
    assert count(session, Account) == 1 and count(session, EmailAddressQuota) == 2
    confirm_email(session, original.token)
    clock[0] = T0 + timedelta(hours=2)
    assert register(session, policy, "new@example.test") is not None
    assert count(session, EmailAddressQuota) == 1


def test_purge_is_bounded_and_does_not_remove_live_windows(session, policy):
    for i in range(40):
        session.add(
            EmailAddressQuota(
                address_digest=f"{i:064x}",
                purpose="reset",
                window_started_at=T0 - timedelta(hours=4),
                last_admitted_at=T0 - timedelta(hours=3),
                expires_at=T0 - timedelta(hours=1),
                admitted=1,
                admissions=[T0 - timedelta(hours=3)],
            )
        )
    session.flush()
    request_password_reset(session, "missing@example.test", policy=policy)
    assert count(session, EmailAddressQuota) == 9
    request_password_reset(session, "othermissing@example.test", policy=policy)
    assert count(session, EmailAddressQuota) == 2


def test_full_rollback_restores_password_proof_and_budget(session, policy):
    verified(session, policy)
    reset = request_password_reset(session, EMAIL, policy=policy).intent
    session.commit()
    budget_before = session.get(EmailBudget, 1).day_count
    complete_password_reset(session, reset.token, NEW)
    session.rollback()
    assert session.get(EmailBudget, 1).day_count == budget_before
    assert verify_password(session.scalar(select(PasswordCredential)).password_hash, PASSWORD)
    complete_password_reset(session, reset.token, NEW)
    session.commit()
    assert auth.authenticate(session, EMAIL, NEW)


def test_pg_constraints_and_transaction_remain_usable(session, policy):
    register(session, policy)
    for sql in [
        "UPDATE auth_challenge SET purpose='session'",
        "UPDATE auth_challenge SET credential_version=0",
        "UPDATE auth_challenge SET token_digest='raw-token'",
        "UPDATE auth_challenge SET expires_at=created_at",
        "UPDATE email_budget SET id=2",
        "UPDATE email_address_quota SET admitted=0",
        "UPDATE email_address_quota SET purpose='session'",
    ]:
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.execute(text(sql))
    assert count(session, AuthChallenge) == 1


def wait_blocked(database, pid):
    deadline = time.monotonic() + 5
    with database.connect() as observer:
        while time.monotonic() < deadline:
            if (
                observer.scalar(text("SELECT cardinality(pg_blocking_pids(:pid))"), {"pid": pid})
                > 0
            ):
                return
            time.sleep(0.01)
    pytest.fail("Second PostgreSQL connection did not wait on first transaction")


def concurrent_after(session, database, second):
    """First operation has executed, holds its locks but has not committed."""
    pids = Queue()

    def run():
        with Session(database) as other:
            other.execute(text("SET LOCAL statement_timeout='8s'"))
            pids.put(other.scalar(select(func.pg_backend_pid())))
            try:
                result = second(other)
            except (AuthenticationFailed, InvalidProof):
                other.rollback()
                return "denied"
            other.commit()
            return result

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run)
        try:
            wait_blocked(database, pids.get(timeout=5))
        finally:
            session.commit()
        return future.result(timeout=10)


def test_same_email_registration_two_connections_serialize_and_bind_latest_hash(
    session, database, policy
):
    first = register(session, policy)
    second = concurrent_after(
        session,
        database,
        lambda other: request_registration(other, EMAIL, NEW, policy=policy).intent,
    )
    with pytest.raises(InvalidProof):
        confirm_email(session, first.token)
    confirm_email(session, second.token)
    assert auth.authenticate(session, EMAIL, NEW)
    assert count(session, Account) == 1 and session.get(EmailBudget, 1).day_count == 2


@pytest.mark.parametrize("purpose", ["confirmation", "reset"])
def test_double_consumption_two_connections_has_one_durable_success(
    session, database, policy, purpose
):
    if purpose == "confirmation":
        intent = register(session, policy)

        def consume(s):
            return confirm_email(s, intent.token)
    else:
        verified(session, policy)
        intent = request_password_reset(session, EMAIL, policy=policy).intent

        def consume(s):
            return complete_password_reset(s, intent.token, NEW)

    session.commit()
    consume(session)
    assert concurrent_after(session, database, consume) == "denied"
    assert count(session, AuthChallenge) == 0


def test_global_budget_two_new_accounts_no_unused_pending_and_no_lost_counter(
    session, database, policy
):
    policy = replace(policy, per_day=1)
    first = register(session, policy)
    assert (
        concurrent_after(
            session, database, lambda other: register(other, policy, "other@example.test")
        )
        is None
    )
    assert count(session, Account) == count(session, PasswordCredential) == 1
    assert session.scalar(select(Account.email_normalized)) == first.recipient
    assert session.get(EmailBudget, 1).day_count == 1


@pytest.mark.parametrize("second", ["old_login", "fresh_login", "change", "revoke", "delete"])
def test_reset_first_serializes_login_change_revoke_delete(session, database, policy, second):
    verified(session, policy)
    account_id = session.scalar(select(Account.id))
    grant = auth.authenticate(session, EMAIL, PASSWORD)
    intent = request_password_reset(session, EMAIL, policy=policy).intent
    session.commit()
    complete_password_reset(session, intent.token, NEW)

    def operation(other):
        if second in {"old_login", "fresh_login"}:
            return auth.authenticate(
                other, EMAIL, NEW if second == "fresh_login" else PASSWORD
            ).token
        if second == "change":
            auth.change_password(other, grant.token, PASSWORD, " Third Exact Passphrase 2028 ")
        elif second == "revoke":
            auth.logout_all(other, grant.token)
        else:
            delete_account(other, other.get(Account, account_id))
        return "done"

    result = concurrent_after(session, database, operation)
    if second in {"old_login", "change", "revoke"}:
        assert result == "denied"
    elif second == "delete":
        assert result == "done" and count(session, Account) == count(session, AuthSession) == 0
    else:
        assert auth.resolve_session(session, result)
    assert count(session, AuthChallenge) == 0


@pytest.mark.parametrize("first", ["login", "change", "revoke", "delete"])
def test_prior_login_change_revoke_delete_serializes_reset(session, database, policy, first):
    verified(session, policy)
    account_id = session.scalar(select(Account.id))
    grant = auth.authenticate(session, EMAIL, PASSWORD)
    reset = request_password_reset(session, EMAIL, policy=policy).intent
    session.commit()
    if first == "login":
        prior = auth.authenticate(session, EMAIL, PASSWORD)
    elif first == "change":
        auth.change_password(session, grant.token, PASSWORD, NEW)
    elif first == "revoke":
        auth.logout_all(session, grant.token)
    else:
        delete_account(session, session.get(Account, account_id))
    result = concurrent_after(
        session, database, lambda other: complete_password_reset(other, reset.token, NEW)
    )
    if first == "login":
        assert result is None
        with pytest.raises(AuthenticationFailed):
            auth.resolve_session(session, prior.token)
    else:
        assert result == "denied"


@pytest.mark.parametrize("join_mode", ["create_savepoint", "rollback_only", "control_fully"])
def test_external_connection_session_is_rejected_before_mutation(database, policy, join_mode):
    with database.connect() as connection:
        transaction = connection.begin()
        try:
            with RawSession(bind=connection, join_transaction_mode=join_mode) as external:
                with pytest.raises(FlowConfigurationError):
                    request_registration(external, EMAIL, PASSWORD, policy=policy)
                assert external.scalar(select(func.count()).select_from(Account)) == 0
                assert external.scalar(select(func.count()).select_from(EmailBudget)) == 0
        finally:
            if transaction.is_active:
                transaction.rollback()


@pytest.mark.parametrize("ending", ["rollback", "close"])
def test_intent_before_nested_rollback_survives_but_inside_does_not(session, policy, ending):
    outer = register(session, policy)
    nested = session.begin_nested()
    inner = register(session, policy, "inside@example.test")
    if ending == "rollback":
        nested.rollback()
    else:
        nested.close()
    session.commit()
    service = EmailService.from_environment(
        {"APP_BASE_URL": "https://site.example.test", "RACEATLAS_ENV": "test"}
    )
    assert outer.dispatch_after_commit(service).status == "simulated"
    with pytest.raises(EmailIntentUnavailable):
        inner.dispatch_after_commit(service)


def test_session_close_then_reuse_commit_cannot_arm_abandoned_intent(session, policy):
    intent = register(session, policy)
    session.close()
    session.commit()
    service = EmailService.from_environment(
        {"APP_BASE_URL": "https://site.example.test", "RACEATLAS_ENV": "test"}
    )
    with pytest.raises(EmailIntentUnavailable):
        intent.dispatch_after_commit(service)
    assert count(session, Account) == 0


def test_hourly_limit_is_sliding_at_window_boundary(session, clock):
    policy = FlowPolicy(KEY, cooldown_seconds=0)
    register(session, policy)
    for seconds in [3598, 3599, 3600]:
        clock[0] = T0 + timedelta(seconds=seconds)
        assert resend_confirmation(session, EMAIL, policy=policy).intent is not None
    clock[0] = T0 + timedelta(seconds=3601)
    assert resend_confirmation(session, EMAIL, policy=policy).intent is None
    clock[0] = T0 + timedelta(seconds=7200)
    assert resend_confirmation(session, EMAIL, policy=policy).intent is not None
    assert session.scalar(select(EmailAddressQuota)).admitted == 1


def test_autocommit_engine_is_rejected_before_mutation(database, policy):
    engine = database.execution_options(isolation_level="AUTOCOMMIT")
    with Session(engine) as unsafe:
        with pytest.raises(FlowConfigurationError):
            request_registration(unsafe, EMAIL, PASSWORD, policy=policy)
    with Session(database) as check:
        assert count(check, Account) == count(check, EmailBudget) == 0


@pytest.mark.parametrize("join_mode", ["create_savepoint", "rollback_only"])
@pytest.mark.parametrize(
    "operation", ["register", "resend", "request_reset", "confirm", "complete_reset"]
)
def test_engine_bound_raw_session_with_enlisted_external_connection_is_rejected(
    database, policy, join_mode, operation
):
    with database.connect() as connection:
        outer = connection.begin()
        try:
            with RawSession(database, join_transaction_mode=join_mode) as raw:
                raw.connection(bind_arguments={"bind": connection})
                assert raw.get_bind(mapper=Account) is database
                calls = {
                    "register": lambda: request_registration(raw, EMAIL, PASSWORD, policy=policy),
                    "resend": lambda: resend_confirmation(raw, EMAIL, policy=policy),
                    "request_reset": lambda: request_password_reset(raw, EMAIL, policy=policy),
                    "confirm": lambda: confirm_email(raw, "A" * 43),
                    "complete_reset": lambda: complete_password_reset(raw, "A" * 43, NEW),
                }
                with pytest.raises(FlowConfigurationError):
                    calls[operation]()
                assert outer.is_active
                assert raw.info.get("account_flow_intents", []) == []
                assert (
                    count(raw, Account) == count(raw, AuthChallenge) == count(raw, EmailBudget) == 0
                )
                raw.commit()
                assert outer.is_active
                with RawSession(database) as observer:
                    assert count(observer, Account) == count(observer, EmailBudget) == 0
        finally:
            if outer.is_active:
                outer.rollback()


def test_raw_engine_session_also_refused_before_mutation(database, policy):
    with RawSession(database) as raw:
        with pytest.raises(FlowConfigurationError):
            request_registration(raw, EMAIL, PASSWORD, policy=policy)
        assert not raw.in_transaction()


@pytest.mark.parametrize("target_kind", ["connection", "other_engine"])
@pytest.mark.parametrize(
    "api",
    ["connection", "execute", "scalars", "scalar", "transaction", "mapper", "table", "constructor"],
)
def test_flow_session_refuses_all_public_bind_routing_before_mutation(
    database, policy, target_kind, api
):
    with database.connect() as connection:
        outer = connection.begin()
        target = connection if target_kind == "connection" else database.execution_options()
        try:
            with AccountFlowSession(database) as session:
                if api == "transaction":
                    session.begin()
                calls = {
                    "connection": lambda: session.connection(bind_arguments={"bind": target}),
                    "execute": lambda: session.execute(
                        text("SELECT 1"), bind_arguments={"bind": target}
                    ),
                    "scalars": lambda: session.scalars(
                        select(Account), bind_arguments={"bind": target}
                    ),
                    "scalar": lambda: session.scalar(
                        select(func.count()).select_from(Account), bind_arguments={"bind": target}
                    ),
                    "transaction": lambda: session.get_transaction().connection(None, bind=target),
                    "mapper": lambda: session.bind_mapper(Account, target),
                    "table": lambda: session.bind_table(Account.__table__, target),
                    "constructor": lambda: AccountFlowSession(database, binds={Account: target}),
                }
                with pytest.raises(FlowConfigurationError):
                    calls[api]()
                assert outer.is_active
                assert count(session, Account) == count(session, EmailBudget) == 0
                # Rejected routing does not poison the supported session/transaction.
                intent = register(session, policy)
                session.commit()
                session.close()
                service = EmailService.from_environment(
                    {"APP_BASE_URL": "https://site.example.test", "RACEATLAS_ENV": "test"}
                )
                assert intent.dispatch_after_commit(service).status == "simulated"
                with RawSession(database) as observer:
                    assert count(observer, Account) == 1
        finally:
            if outer.is_active:
                outer.rollback()


def test_flow_session_bind_assignment_is_rejected_without_enlisting_connection(database, policy):
    with database.connect() as connection, AccountFlowSession(database) as session:
        session.bind = connection
        with pytest.raises(FlowConfigurationError):
            register(session, policy)
        assert not connection.in_transaction() and not session.in_transaction()
