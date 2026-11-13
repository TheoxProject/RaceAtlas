import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Event

import pytest
import requests
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from raceatlas import create_app
from raceatlas.auth import flows
from raceatlas.auth.dispatch import stop_process_dispatcher
from raceatlas.auth.flow_limits import FlowPolicy
from raceatlas.auth.flows import AccountFlowSession
from raceatlas.models import (
    Account,
    AuthAdmissionBucket,
    AuthAdmissionState,
    AuthChallenge,
    AuthSession,
    EmailAddressQuota,
    EmailBudget,
    PasswordCredential,
)

ORIGIN = "http://127.0.0.1"
PASSWORD = " Synthetic Chosen Passphrase 2026 "
NEW = " Replacement Exact Passphrase 2027 "
CSRF = "synthetic-csrf-key-distinct-000000000"
RATE = "synthetic-rate-key-distinct-111111111"


@pytest.fixture(autouse=True)
def clean(database, monkeypatch):
    assert stop_process_dispatcher(5)
    with database.begin() as connection:
        for model in (
            Account,
            EmailAddressQuota,
            EmailBudget,
            AuthAdmissionBucket,
            AuthAdmissionState,
        ):
            connection.execute(delete(model))

    def forbidden(*args, **kwargs):
        raise AssertionError("Real email network forbidden")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    yield
    assert stop_process_dispatcher(5)


@pytest.fixture
def app_factory(database):
    apps = []

    def factory(*, fast=True, **patch):
        app = create_app(
            {
                "ENVIRONMENT": "test",
                "DATABASE_URL": database.url,
                "AUTH_ENABLED": True,
                "AUTH_CSRF_KEY": CSRF,
                "AUTH_RATE_KEY": RATE,
                "APP_BASE_URL": ORIGIN,
                "EMAIL_PROVIDER": "development",
                **patch,
            }
        )
        if fast:
            runtime = app.extensions["auth"]
            runtime.settings = replace(
                runtime.settings,
                rate_policy=FlowPolicy(RATE.encode(), cooldown_seconds=0, per_hour=20),
            )
        apps.append(app)
        return app

    yield factory
    for app in apps:
        assert app.extensions["auth"].close(timeout=5)
        app.extensions["database"].dispose()


@pytest.fixture
def app(app_factory):
    return app_factory()


def send(client, path, body, *, proof=None):
    csrf = client.get("/api/v1/auth/csrf", base_url=ORIGIN)
    assert csrf.status_code == 200
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf.json["csrf_token"]}
    if proof is not None:
        headers["X-Account-Proof"] = proof
    return client.post("/api/v1/auth/" + path, json=body, headers=headers, base_url=ORIGIN)


def register(client, email="alice@example.test", password=PASSWORD):
    return send(client, "register", {"email": email, "password": password})


def login(client, email="alice@example.test", password=PASSWORD):
    return send(client, "login", {"email": email, "password": password})


def bearer(client):
    cookie = client.get_cookie("raceatlas_session_dev", domain="127.0.0.1")
    return None if cookie is None else cookie.value


def messages(app):
    runtime = app.extensions["auth"]
    assert runtime.drain(5)
    return runtime.email_service()._provider.messages


def token(message):
    return re.search(r"#(?:confirm-email|reset-password)=([A-Za-z0-9_-]{43})", message.text).group(
        1
    )


def verify_account(app, client, email="alice@example.test"):
    assert register(client, email).status_code == 202
    proof = token(messages(app)[-1])
    assert send(client, "confirmation/complete", {}, proof=proof).status_code == 204
    return proof


def count(database, model):
    with Session(database) as session:
        return session.scalar(select(func.count()).select_from(model))


def test_real_register_confirmation_login_reset_revokes_devices_no_auto_login(app, database):
    client, device = app.test_client(), app.test_client()
    response = register(client)
    assert response.status_code == 202 and response.json == {"status": "accepted"}
    assert bearer(client) is None
    proof = token(messages(app)[-1])
    with Session(database) as session:
        row = session.scalar(select(AuthChallenge))
        assert row.expires_at - row.created_at == timedelta(hours=24)
        assert row.token_digest == flows._digest("confirmation", proof)
        assert proof not in row.token_digest
    assert login(client).status_code == 401
    assert send(client, "confirmation/complete", {}, proof=proof).status_code == 204
    assert (
        bearer(client) is None
        and send(client, "confirmation/complete", {}, proof=proof).status_code == 400
    )
    assert login(client).status_code == login(device).status_code == 200
    old = bearer(client)
    assert (
        send(client, "password-reset/request", {"email": "alice@example.test"}).status_code == 202
    )
    reset = token(messages(app)[-1])
    assert count(database, AuthSession) == 2
    with Session(database) as session:
        row = session.scalar(select(AuthChallenge))
        assert row.expires_at - row.created_at == timedelta(minutes=30)
    response = send(client, "password-reset/complete", {"new_password": NEW}, proof=reset)
    assert (
        response.status_code == 204
        and "Set-Cookie" not in response.headers
        and bearer(client) == old
    )
    assert count(database, AuthSession) == 0
    assert device.get("/api/v1/me", base_url=ORIGIN).status_code == 401
    assert (
        send(client, "password-reset/complete", {"new_password": PASSWORD}, proof=reset).status_code
        == 400
    )
    assert login(client, password=NEW).status_code == 200


def test_reset_account_b_under_cookie_a_preserves_a_and_targets_only_proof(app, database):
    alice, bob = app.test_client(), app.test_client()
    verify_account(app, alice)
    verify_account(app, bob, "bob@example.test")
    assert login(alice).status_code == 200 and login(bob, "bob@example.test").status_code == 200
    alice_cookie = bearer(alice)
    assert send(alice, "password-reset/request", {"email": "bob@example.test"}).status_code == 202
    proof = token(messages(app)[-1])
    response = send(alice, "password-reset/complete", {"new_password": NEW}, proof=proof)
    assert response.status_code == 204 and "Set-Cookie" not in response.headers
    assert (
        bearer(alice) == alice_cookie
        and alice.get("/api/v1/me", base_url=ORIGIN).json["account"]["email"]
        == "alice@example.test"
    )
    assert bob.get("/api/v1/me", base_url=ORIGIN).status_code == 401
    assert count(database, AuthSession) == 1
    assert login(bob, "bob@example.test", NEW).status_code == 200


def test_resend_replacement_confirmed_nonoverwrite_and_uniform_unknown(app, database):
    client = app.test_client()
    assert register(client).status_code == 202
    first = token(messages(app)[-1])
    assert send(client, "confirmation/resend", {"email": "alice@example.test"}).status_code == 202
    current = token(messages(app)[-1])
    assert send(client, "confirmation/complete", {}, proof=first).status_code == 400
    assert send(client, "confirmation/complete", {}, proof=current).status_code == 204
    with Session(database) as session:
        before = session.scalar(select(PasswordCredential.password_hash))
    assert register(client, password=NEW).status_code == 202
    assert send(client, "confirmation/resend", {"email": "alice@example.test"}).status_code == 202
    assert (
        send(client, "password-reset/request", {"email": "unknown@example.test"}).status_code == 202
    )
    assert len(messages(app)) == 2
    with Session(database) as session:
        assert session.scalar(select(PasswordCredential.password_hash)) == before


def test_default_cooldown_refusal_keeps_active_proof_and_reserved_budget(app_factory, database):
    app = app_factory(fast=False)
    client = app.test_client()
    assert register(client).status_code == 202
    proof = token(messages(app)[-1])
    assert send(client, "confirmation/resend", {"email": "alice@example.test"}).json == {
        "status": "accepted"
    }
    assert len(messages(app)) == 1
    with Session(database) as session:
        assert session.get(EmailBudget, 1).day_count == 1
    assert send(client, "confirmation/complete", {}, proof=proof).status_code == 204


@pytest.mark.parametrize(
    "path,body",
    [
        ("register", {"email": "é@example.test", "password": PASSWORD}),
        ("register", {"email": "alice@example.test", "password": "short"}),
        ("confirmation/complete", {"token": "A" * 43}),
        ("password-reset/complete", {"new_password": "short"}),
    ],
)
def test_invalid_perimeter_does_not_create_account_or_proof(app, database, path, body):
    response = send(app.test_client(), path, body)
    assert response.status_code == 400
    assert count(database, Account) == count(database, AuthChallenge) == 0


def test_provider_slow_or_failing_never_blocks_http_or_changes_202(app, monkeypatch):
    runtime = app.extensions["auth"]
    provider = runtime.email_service()._provider
    entered, release = Event(), Event()

    def slow(message, operation):
        entered.set()
        assert release.wait(5)
        raise RuntimeError("synthetic provider secret must not be logged")

    monkeypatch.setattr(provider, "send", slow)
    response = register(app.test_client())
    try:
        assert response.status_code == 202 and entered.wait(3)
        unknown = send(
            app.test_client(), "password-reset/request", {"email": "absent@example.test"}
        )
        assert unknown.status_code == 202 and unknown.json == response.json
        assert app.test_client().get("/api/health/live").status_code == 200
    finally:
        release.set()
    assert runtime.drain(5)
    assert runtime._channel.manager.counts["failed"] == 1


def test_commit_failure_never_enqueues_or_publishes_an_intent(app, database, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError

    import raceatlas.auth.email_http as http

    original = http.AccountFlowSession

    class BrokenCommit(original):
        def commit(self):
            raise SQLAlchemyError("synthetic failure")

    monkeypatch.setattr(http, "AccountFlowSession", BrokenCommit)
    assert register(app.test_client()).status_code == 503
    assert app.extensions["auth"]._channel is None
    assert count(database, Account) == count(database, AuthChallenge) == 0


def test_legacy_email_intent_keeps_operation_id_position_but_cannot_enter_http_queue(app, database):
    from uuid import uuid4

    operation = uuid4()
    legacy = flows.EmailIntent("confirmation", "legacy@example.test", "A" * 43, operation)
    assert legacy.operation_id == operation and legacy.account_id is None
    with AccountFlowSession(database) as session:
        session.scalar(select(func.clock_timestamp()))
        flows._track(session, legacy)
        session.commit()
    runtime = app.extensions["auth"]
    assert not runtime.enqueue_email(app.extensions["database"], legacy)
    assert legacy.dispatch_after_commit(runtime.email_service()).status == "simulated"
    assert len(runtime.email_service()._provider.messages) == 1


def make_intent(database, app, email="job@example.test"):
    with AccountFlowSession(database) as session:
        result = flows.request_registration(
            session, email, PASSWORD, policy=app.extensions["auth"].settings.rate_policy
        )
        session.commit()
        return result.intent


def test_global_capacity_closed_queue_and_stop_incomplete_are_bounded(
    app, app_factory, database, monkeypatch
):
    runtime = app.extensions["auth"]
    provider = runtime.email_service()._provider
    entered, release = Event(), Event()
    original = provider.send

    def slow(message, operation):
        entered.set()
        assert release.wait(10)
        return original(message, operation)

    monkeypatch.setattr(provider, "send", slow)
    first = make_intent(database, app)
    assert runtime.enqueue_email(app.extensions["database"], first)
    try:
        assert entered.wait(3)
        for i in range(16):
            assert runtime.enqueue_email(
                app.extensions["database"], make_intent(database, app, f"queued{i}@example.test")
            )
        overflow = make_intent(database, app, "overflow@example.test")
        assert not runtime.enqueue_email(app.extensions["database"], overflow)
        manager = runtime._channel.manager
        with manager.condition:
            assert len(manager.pending) == 16 and manager.active is not None
        response = register(app.test_client(), "overflow-http@example.test")
        assert response.status_code == 202 and response.json == {"status": "accepted"}
        assert not runtime.close(0.01)
        with manager.condition:
            assert not manager.pending and manager.active is not None
        other = app_factory()
        assert register(other.test_client(), "new-channel@example.test").status_code == 202
        assert other.extensions["auth"]._channel is None
        from threading import enumerate as threads

        assert len([thread for thread in threads() if thread.name == "raceatlas-email"]) == 1
    finally:
        release.set()
    assert runtime.close(5)
    assert len(provider.messages) == 1


def test_two_apps_share_one_worker_isolate_services_and_keep_global_cadence(
    app_factory, database, monkeypatch
):
    import time

    one, two = app_factory(), app_factory()
    first, second = one.extensions["auth"], two.extensions["auth"]
    starts = []
    for runtime in (first, second):
        provider = runtime.email_service()._provider
        original = provider.send

        def observe(message, operation, original=original):
            starts.append(time.monotonic())
            return original(message, operation)

        monkeypatch.setattr(provider, "send", observe)
    assert first.enqueue_email(
        one.extensions["database"], make_intent(database, one, "one@example.test")
    )
    assert second.enqueue_email(
        two.extensions["database"], make_intent(database, two, "two@example.test")
    )
    assert first._channel.manager is second._channel.manager
    assert first.drain(5) and second.drain(5)
    assert starts[1] - starts[0] >= 0.2
    assert [message.recipient for message in first.email_service()._provider.messages] == [
        "one@example.test"
    ]
    assert [message.recipient for message in second.email_service()._provider.messages] == [
        "two@example.test"
    ]
    assert first.close(1)
    assert second.enqueue_email(
        two.extensions["database"], make_intent(database, two, "still-open@example.test")
    )
    assert second.drain(5)
    assert len(second.email_service()._provider.messages) == 2


@pytest.mark.parametrize(
    "stale",
    ["consumed", "replaced", "expired", "version", "deleted", "account", "purpose", "recipient"],
)
def test_worker_drops_stale_or_misbound_proofs_without_consumption_or_transport(
    app, database, stale
):
    import copy

    intent = make_intent(database, app)
    with AccountFlowSession(database) as session:
        if stale == "consumed":
            flows.confirm_email(session, intent.token)
        elif stale == "replaced":
            flows.resend_confirmation(
                session, intent.recipient, policy=app.extensions["auth"].settings.rate_policy
            )
        elif stale == "expired":
            row = session.scalar(select(AuthChallenge))
            row.created_at = datetime.now(timezone.utc) - timedelta(days=2)
            row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        elif stale == "version":
            session.get(PasswordCredential, intent.account_id).session_version += 1
        elif stale == "deleted":
            session.delete(session.get(Account, intent.account_id))
        else:
            intent = copy.copy(intent)
            if stale == "account":
                intent.account_id = "another-opaque-account"
            if stale == "purpose":
                intent.purpose = "reset"
            if stale == "recipient":
                intent.recipient = "someoneelse@example.test"
        session.commit()
    runtime = app.extensions["auth"]
    before = count(database, AuthChallenge)
    assert runtime.enqueue_email(app.extensions["database"], intent)
    assert runtime.drain(5)
    assert runtime.email_service()._provider.messages == ()
    assert count(database, AuthChallenge) == before
    assert runtime._channel.manager.counts["dropped"] == 1


def test_probe_has_no_open_transaction_at_provider_and_worker_releases_idle_refs(
    app, database, monkeypatch
):
    import gc
    import weakref
    from threading import current_thread

    from sqlalchemy import create_engine, event, text

    from raceatlas.auth.dispatch import open_channel

    service = app.extensions["auth"].email_service()
    provider = service._provider
    observer = create_engine(database.url)
    pids = []
    observed = []

    def began(session, transaction, connection):
        if current_thread().name == "raceatlas-email":
            pids.append(connection.scalar(select(func.pg_backend_pid())))

    original = provider.send

    def verify(message, operation):
        with observer.connect() as connection:
            state = connection.execute(
                text("SELECT state,xact_start FROM pg_stat_activity WHERE pid=:pid"),
                {"pid": pids[-1]},
            ).one()
            assert state.state == "idle" and state.xact_start is None
        observed.append(True)
        return original(message, operation)

    monkeypatch.setattr(provider, "send", verify)
    event.listen(AccountFlowSession, "after_begin", began)
    channel = None
    try:
        intent = make_intent(database, app)
        ref = weakref.ref(intent)
        channel = open_channel(app.extensions["database"], service)
        assert channel.enqueue(intent)
        del intent
        assert channel.drain(5) and observed == [True]
        gc.collect()
        assert ref() is None
        channel_ref = weakref.ref(channel)
        assert channel.close(5)
        del channel
        channel = None
        gc.collect()
        assert channel_ref() is None
    finally:
        event.remove(AccountFlowSession, "after_begin", began)
        if channel is not None:
            assert channel.close(5)
        observer.dispose()


def test_slow_probe_does_not_hold_queue_lock_or_block_enqueue_and_delete(
    app, database, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor

    import raceatlas.auth.dispatch as dispatch

    client = app.test_client()
    verify_account(app, client)
    assert login(client).status_code == 200
    entered, release = Event(), Event()
    original = dispatch._active

    def slow(job):
        entered.set()
        assert release.wait(10)
        return original(job)

    monkeypatch.setattr(dispatch, "_active", slow)
    assert (
        send(client, "password-reset/request", {"email": "alice@example.test"}).status_code == 202
    )
    try:
        assert entered.wait(3)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(register, app.test_client(), "bob@example.test")
            assert future.result(timeout=5).status_code == 202
        csrf = client.get("/api/v1/auth/csrf", base_url=ORIGIN).json["csrf_token"]
        response = client.delete(
            "/api/v1/me",
            base_url=ORIGIN,
            json={"current_password": PASSWORD},
            headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        )
        assert response.status_code == 204 and not release.is_set()
    finally:
        release.set()
    assert app.extensions["auth"].drain(5)
    assert [message.recipient for message in messages(app)] == [
        "alice@example.test",
        "bob@example.test",
    ]


def test_provider_quota_failure_is_one_attempt_not_retry_and_probe_db_error_drops(
    app, database, monkeypatch, caplog
):
    import raceatlas.auth.dispatch as dispatch
    from raceatlas.email.config import EmailDeliveryError

    runtime = app.extensions["auth"]
    provider = runtime.email_service()._provider
    calls = []

    def quota(*args, **kwargs):
        calls.append(1)
        raise EmailDeliveryError("quota")

    monkeypatch.setattr(provider, "send", quota)
    assert register(app.test_client()).status_code == 202
    assert runtime.drain(5) and calls == [1]
    from sqlalchemy.exc import SQLAlchemyError

    def unavailable(*args, **kwargs):
        raise SQLAlchemyError("synthetic DSN token must stay private")

    monkeypatch.setattr(dispatch, "email_intent_is_active", unavailable)
    assert register(app.test_client(), "other@example.test").status_code == 202
    assert runtime.drain(5) and calls == [1]
    assert "synthetic DSN" not in caplog.text


@pytest.mark.parametrize(
    "branch", ["new", "pending", "confirmed", "future", "limited", "budget", "capacity"]
)
def test_registration_performs_exactly_one_native_kdf_per_normal_result(
    app_factory, database, monkeypatch, branch
):
    import raceatlas.auth.passwords as passwords

    app = app_factory(fast=branch != "limited")
    runtime = app.extensions["auth"]
    if branch in {"pending", "confirmed", "future", "limited"}:
        initial = make_intent(database, app, "alice@example.test")
        if branch in {"confirmed", "future"}:
            with Session(database) as session, session.begin():
                session.get(PasswordCredential, initial.account_id).email_verified_at = (
                    datetime(2020, 1, 1, tzinfo=timezone.utc)
                    if branch == "confirmed"
                    else datetime(2099, 1, 1, tzinfo=timezone.utc)
                )
    elif branch == "budget":
        now = datetime.now(timezone.utc)
        with Session(database) as session, session.begin():
            session.add(
                EmailBudget(
                    id=1,
                    day=now.date(),
                    month=now.date().replace(day=1),
                    day_count=80,
                    month_count=80,
                )
            )
    elif branch == "capacity":
        runtime.settings = replace(
            runtime.settings, rate_policy=replace(runtime.settings.rate_policy, capacity=1)
        )
        with AccountFlowSession(database) as session:
            flows.request_password_reset(
                session, "absent@example.test", policy=runtime.settings.rate_policy
            )
            session.commit()
    original = passwords._hasher
    calls = []

    class Proxy:
        def hash(self, *args, **kwargs):
            calls.append("hash")
            return original.hash(*args, **kwargs)

        def verify(self, *args, **kwargs):
            calls.append("verify")
            return original.verify(*args, **kwargs)

    monkeypatch.setattr(passwords, "_hasher", Proxy())
    from time import perf_counter

    started = perf_counter()
    response = register(app.test_client())
    elapsed_ms = (perf_counter() - started) * 1000
    assert response.status_code == 202 and runtime.drain(5)
    assert calls == (["hash"] if branch in {"new", "pending"} else ["verify"])
    import json
    from pathlib import Path

    result = Path(".local-tools/c2-registration-profiles.jsonl")
    result.parent.mkdir(exist_ok=True, parents=True)
    with result.open("a", encoding="utf-8") as output:
        output.write(
            json.dumps(
                {
                    "branch": branch,
                    "milliseconds": round(elapsed_ms, 2),
                    "native_kdf_calls": len(calls),
                    "network": False,
                }
            )
            + "\n"
        )


def test_delete_cancels_pending_old_account_preserves_new_account_same_email(
    app, database, monkeypatch
):
    client = app.test_client()
    verify_account(app, client)
    assert login(client).status_code == 200
    with Session(database) as session:
        old = session.scalar(
            select(Account.id).where(Account.email_normalized == "alice@example.test")
        )
    runtime = app.extensions["auth"]
    provider = runtime.email_service()._provider
    entered, release = Event(), Event()
    original = provider.send

    def slow(message, operation):
        entered.set()
        assert release.wait(10)
        return original(message, operation)

    monkeypatch.setattr(provider, "send", slow)
    assert register(app.test_client(), "blocker@example.test").status_code == 202
    try:
        assert entered.wait(3)
        assert (
            send(client, "password-reset/request", {"email": "alice@example.test"}).status_code
            == 202
        )
        csrf = client.get("/api/v1/auth/csrf", base_url=ORIGIN).json["csrf_token"]
        assert (
            client.delete(
                "/api/v1/me",
                base_url=ORIGIN,
                json={"current_password": PASSWORD},
                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
            ).status_code
            == 204
        )
        with runtime._channel.manager.condition:
            assert all(job.intent.account_id != old for job in runtime._channel.manager.pending)
        assert register(app.test_client()).status_code == 202
        with Session(database) as session:
            new = session.scalar(
                select(Account.id).where(Account.email_normalized == "alice@example.test")
            )
        assert new != old
        with runtime._channel.manager.condition:
            assert [job.intent.account_id for job in runtime._channel.manager.pending] == [new]
    finally:
        release.set()
    assert runtime.drain(5)
    assert [message.subject for message in provider.messages].count(
        "Réinitialisez votre mot de passe — RaceAtlas"
    ) == 0
    assert [message.recipient for message in provider.messages].count("alice@example.test") == 2


def test_delete_after_probe_can_finish_inflight_but_proof_is_invalid(app, database, monkeypatch):
    client = app.test_client()
    verify_account(app, client)
    assert login(client).status_code == 200
    runtime = app.extensions["auth"]
    provider = runtime.email_service()._provider
    entered, release = Event(), Event()
    original = provider.send

    def slow(message, operation):
        entered.set()
        assert release.wait(10)
        return original(message, operation)

    monkeypatch.setattr(provider, "send", slow)
    assert (
        send(client, "password-reset/request", {"email": "alice@example.test"}).status_code == 202
    )
    try:
        assert entered.wait(3)
        csrf = client.get("/api/v1/auth/csrf", base_url=ORIGIN).json["csrf_token"]
        assert (
            client.delete(
                "/api/v1/me",
                base_url=ORIGIN,
                json={"current_password": PASSWORD},
                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
            ).status_code
            == 204
        )
    finally:
        release.set()
    assert runtime.drain(5)
    proof = token(provider.messages[-1])
    assert (
        send(
            app.test_client(), "password-reset/complete", {"new_password": NEW}, proof=proof
        ).status_code
        == 400
    )
    assert count(database, Account) == count(database, AuthChallenge) == 0


def test_other_channel_pending_deleted_account_is_dropped_by_pg_check(
    app, app_factory, database, monkeypatch
):
    client = app.test_client()
    verify_account(app, client)
    assert login(client).status_code == 200
    other = app_factory()
    other_runtime = other.extensions["auth"]
    with AccountFlowSession(database) as session:
        intent = flows.request_password_reset(
            session, "alice@example.test", policy=app.extensions["auth"].settings.rate_policy
        ).intent
        session.commit()
    runtime = app.extensions["auth"]
    provider = runtime.email_service()._provider
    entered, release = Event(), Event()
    original = provider.send

    def slow(message, operation):
        entered.set()
        assert release.wait(10)
        return original(message, operation)

    monkeypatch.setattr(provider, "send", slow)
    assert register(app.test_client(), "blocker@example.test").status_code == 202
    try:
        assert entered.wait(3)
        assert other_runtime.enqueue_email(other.extensions["database"], intent)
        csrf = client.get("/api/v1/auth/csrf", base_url=ORIGIN).json["csrf_token"]
        assert (
            client.delete(
                "/api/v1/me",
                base_url=ORIGIN,
                json={"current_password": PASSWORD},
                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
            ).status_code
            == 204
        )
        with runtime._channel.manager.condition:
            assert any(
                job.channel is other_runtime._channel for job in runtime._channel.manager.pending
            )
    finally:
        release.set()
    assert runtime.drain(5) and other_runtime.drain(5)
    assert other_runtime.email_service()._provider.messages == ()


def test_invalid_forms_and_http_admission_refusals_and_reset_requests_have_zero_kdf(
    app, database, monkeypatch
):
    import raceatlas.auth.passwords as passwords
    from raceatlas.auth.admission import AdmissionPolicy

    original = passwords._hasher

    class Forbidden:
        def hash(self, *args, **kwargs):
            pytest.fail("Unexpected native hash")

        def verify(self, *args, **kwargs):
            pytest.fail("Unexpected native verify")

    monkeypatch.setattr(passwords, "_hasher", Forbidden())
    client = app.test_client()
    assert register(client, password="short").status_code == 400
    assert register(client, "é@example.test").status_code == 400
    assert (
        send(client, "password-reset/request", {"email": "alice@example.test"}).status_code == 202
    )
    app.extensions["auth"].admission_policy = AdmissionPolicy(per_address=1)
    assert register(client).status_code == 429
    assert count(database, Account) == 0
    monkeypatch.setattr(passwords, "_hasher", original)


def test_channels_are_bounded_without_creating_more_workers(app, database):
    from raceatlas.auth.dispatch import MAX_CHANNELS, DispatcherUnavailable, open_channel

    service = app.extensions["auth"].email_service()
    channels = []
    try:
        for _ in range(MAX_CHANNELS):
            channels.append(open_channel(app.extensions["database"], service))
        assert len({channel.identity for channel in channels}) == MAX_CHANNELS
        with pytest.raises(DispatcherUnavailable):
            open_channel(app.extensions["database"], service)
        from threading import enumerate as threads

        assert len([thread for thread in threads() if thread.name == "raceatlas-email"]) == 1
    finally:
        for channel in channels:
            assert channel.close(5)


def test_email_contract_and_get_never_consume_proof_or_return_secret(app, database):
    import json
    from pathlib import Path

    from jsonschema import Draft202012Validator, FormatChecker

    spec = json.loads(
        (Path(__file__).resolve().parents[2] / "contracts/auth.openapi.json").read_text(
            encoding="utf-8"
        )
    )
    client = app.test_client()
    accepted = register(client)
    proof = token(messages(app)[-1])
    headers = {"X-Account-Proof": proof}
    assert (
        client.get(
            "/api/v1/auth/confirmation/complete", headers=headers, base_url=ORIGIN
        ).status_code
        == 405
    )
    assert count(database, AuthChallenge) == 1
    rejected = send(client, "password-reset/complete", {"new_password": NEW}, proof=proof)
    assert rejected.status_code == 400 and proof not in rejected.text
    for response, name in [(accepted, "RequestAccepted"), (rejected, "AccountError")]:
        schema = {"components": spec["components"], "$ref": "#/components/schemas/" + name}
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(response.json)
    assert send(client, "confirmation/complete", {}, proof=proof).status_code == 204
