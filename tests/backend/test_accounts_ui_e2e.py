"""Compiled React -> real Flask/PostgreSQL, synthetic memory email only."""

import json
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from queue import Queue
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
from map_support import (
    camera,
    camera_diagnostic,
    install_camera_diagnostic,
    intercept_map,
    launch,
    set_civil_date,
)
from playwright.sync_api import expect, sync_playwright
from test_auth_http_sessions import PASSWORD, identity
from test_e2e import assert_camera_unchanged, wait_camera_pitch
from test_private_planning import isolation as isolation
from werkzeug.serving import make_server

from raceatlas import create_app
from raceatlas.email.config import EmailDeliveryError

SHOTS = Path(__file__).resolve().parents[2] / ".local-tools" / "accounts-ui-screenshots"
ACCEPTED_TEXT = (
    "Demande prise en compte. Vérifiez votre boîte de réception et vos courriers indésirables ; "
    "si un message vous parvient, suivez ses instructions."
)


@pytest.fixture
def admission_clock(monkeypatch):
    """Only admission's sliding window moves; auth/CSRF/DB/RAF clocks stay real."""
    from raceatlas import auth
    from raceatlas.auth import admission

    global_now = auth._now

    class Clock:
        def __init__(self):
            self._time = datetime.now(timezone.utc)
            self._lock = threading.Lock()

        def now(self, _session=None):
            with self._lock:
                return self._time

        def advance(self, seconds):
            assert type(seconds) is int and seconds > 0
            with self._lock:
                self._time += timedelta(seconds=seconds)

    clock = Clock()
    monkeypatch.setattr(admission, "_now", clock.now)
    yield clock
    assert auth._now is global_now  # Never mutate session/security time globally.


@pytest.fixture
def account_server(database, seeded, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("External email/source network forbidden")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    server = make_server("127.0.0.1", 0, lambda environ, start: [], threaded=True)
    origin = f"http://127.0.0.1:{server.server_port}"
    app = create_app(
        {
            "ENVIRONMENT": "test",
            "DATABASE_URL": database.url,
            "AUTH_ENABLED": True,
            "APP_BASE_URL": origin,
            "EMAIL_PROVIDER": "development",
            "AUTH_CSRF_KEY": "synthetic-csrf-key-distinct-000000000",
            "AUTH_RATE_KEY": "synthetic-rate-key-distinct-111111111",
        }
    )
    runtime = app.extensions["auth"]
    provider = runtime.email_service()._provider
    sent = Queue()
    original = provider.send

    def send(message, operation_id):
        receipt = original(message, operation_id)
        sent.put(message)
        return receipt

    monkeypatch.setattr(provider, "send", send)
    server.app = app
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield origin, sent, app
    server.shutdown()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert runtime.close(timeout=5)
    app.extensions["database"].dispose()


def test_browser_admission_clock_preserves_read_limit_and_recovers(
    admission_clock, account_server, database
):
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from raceatlas.auth.admission import key_digest
    from raceatlas.models import AuthAdmissionBucket

    origin, _, app = account_server
    runtime = app.extensions["auth"]
    assert runtime.admission_policy.per_peer == 20
    assert runtime.admission_policy.per_global == 60
    client = app.test_client()
    start = admission_clock.now()
    # These anonymous401 requests are admitted before auth, exactly like the CI
    # trace; none is a successful authenticated read or a bypass of admission.
    assert [client.get("/api/v1/me", base_url=origin).status_code for _ in range(20)] == [401] * 20
    assert client.get("/api/v1/me", base_url=origin).status_code == 429
    admission_clock.advance(59)
    assert client.get("/api/v1/me", base_url=origin).status_code == 429
    digest = key_digest(runtime.settings.rate_policy.rate_key, "peer", "read", "127.0.0.1")
    with Session(database) as session:
        bucket = session.scalar(
            select(AuthAdmissionBucket).where(
                AuthAdmissionBucket.namespace == "peer", AuthAdmissionBucket.key_digest == digest
            )
        )
        assert bucket.admissions == [start] * 20
        assert bucket.expires_at == start + timedelta(hours=1)  # Denials did not extend it.
    admission_clock.advance(2)
    assert client.get("/api/v1/me", base_url=origin).status_code == 401
    with Session(database) as session:
        bucket = session.get(AuthAdmissionBucket, ("peer", digest))
        assert bucket.admissions == [admission_clock.now()]


def prepare(page, *, mobile=False):
    page.set_viewport_size({"width": 390 if mobile else 1440, "height": 844 if mobile else 960})
    page.set_default_timeout(15000)
    set_civil_date(page, "2026-11-11T12:00:00Z")
    intercept_map(page)


def take_link(sent, purpose, origin):
    message = sent.get(timeout=10)
    match = re.search(
        r"https?://[^\s<>]+#(?:confirm-email|reset-password)=[A-Za-z0-9_-]{43}", message.text
    )
    if match is None or urlsplit(match.group()).netloc != urlsplit(origin).netloc:
        raise AssertionError("Synthetic email link missing or wrong origin")
    if (
        "#confirm-email=" if purpose == "confirmation" else "#reset-password="
    ) not in match.group():
        raise AssertionError("Wrong synthetic proof purpose")
    return match.group()


def navigate_proof(page, link):
    try:
        page.goto(link)
    except Exception:
        # Playwright navigation call logs can include the fragment: never propagate them.
        raise AssertionError("Synthetic proof navigation failed; URL withheld") from None


def account(page):
    page.get_by_role("button", name="Compte", exact=True).click()
    expect(page.locator("dialog.account-dialog")).to_be_visible()
    expect(page.locator(".account-context")).not_to_contain_text("Vérification")


def sign_in(page, email, password):
    if page.get_by_role("button", name="Utiliser un autre compte").count():
        page.get_by_role("button", name="Utiliser un autre compte").click()
    page.get_by_label("Adresse email", exact=True).fill(email)
    page.get_by_label("Mot de passe", exact=True).fill(password)
    page.get_by_role("button", name="Se connecter", exact=True).click()
    expect(page.locator(".account-context")).to_contain_text(email)
    expect(page.get_by_role("heading", name="Mon compte", exact=True)).to_be_visible()


def screenshot(page, name):
    if urlsplit(page.url).fragment:
        raise AssertionError("Fragment not scrubbed before capture")
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / name), timeout=5000)


def select_public_month(page, month, expected_ids):
    """Separate public selection transport from presentation; no private traffic retained."""
    started = time.monotonic()
    trace = {"phase": "public-selection", "month": month, "events": []}
    initial_camera = camera_diagnostic(page)
    trace["camera_before_selection"] = {
        "age_ms": initial_camera.get("host_snapshot_age_ms"),
        "snapshot": initial_camera.get("snapshot"),
    }
    first, last = {"1": ("2026-01-01", "2026-01-31"), "11": ("2026-11-01", "2026-11-30")}[month]
    observed = {}

    def matches(request, kind):
        parsed = urlsplit(request.url)
        path, limit = {
            "races": ("/api/v1/races", "200"),
            "map": ("/api/v1/map", "200"),
            "witness": ("/api/v1/races", "1"),
        }[kind]
        if parsed.path != path:
            return False
        parameters = parse_qs(parsed.query)
        try:
            selection = json.loads(parameters.get("filter", [""])[0])
        except (ValueError, TypeError):
            return False
        return (
            parameters.get("limit") == [limit]
            and selection.get("from") == first
            and selection.get("to") == last
            and selection.get("query") == "race-road-split"
        )

    def record(request, phase, status=None):
        entry = observed.get(request)
        if entry is None:
            kind = next(
                (kind for kind in ("races", "map", "witness") if matches(request, kind)), None
            )
            if kind is None or len(observed) >= 12:
                return
            entry = observed[request] = (kind, len(observed) + 1)
        kind, number = entry
        if len(trace["events"]) < 48:
            trace["events"].append(
                {
                    "request_id": number,
                    "kind": kind,
                    "phase": phase,
                    "status": status,
                    "host_ms": round((time.monotonic() - started) * 1000, 2),
                }
            )

    callbacks = {
        "request": lambda request: record(request, "request"),
        "response": lambda response: record(response.request, "response", response.status),
        "requestfinished": lambda request: record(request, "finished"),
        "requestfailed": lambda request: record(request, "failed"),
    }
    for event, callback in callbacks.items():
        page.on(event, callback)

    try:
        # List/map are parallel; their version witness is a subsequent mandatory fetch.
        # All listeners are armed before selection and each transport budget is explicit.
        with (
            page.expect_event(
                "requestfinished", predicate=lambda r: matches(r, "races"), timeout=15000
            ) as races,
            page.expect_event(
                "requestfinished", predicate=lambda r: matches(r, "map"), timeout=15000
            ) as markers,
            page.expect_event(
                "requestfinished", predicate=lambda r: matches(r, "witness"), timeout=15000
            ) as witness,
        ):
            trace["phase"] = "select-start"
            page.get_by_label("Mois", exact=True).select_option(month)
            trace["select_return_ms"] = round((time.monotonic() - started) * 1000, 2)
            trace["phase"] = "public-selection"
        documents = {}
        for kind, completed in (("races", races), ("map", markers), ("witness", witness)):
            response = completed.value.response()
            # requestfinished already proves completion; Response.finished() in the
            # pinned driver creates redundant tasks that outlive browser teardown.
            if response is None or response.status != 200:
                raise AssertionError("Public selection transport was not completed successfully")
            try:
                document = response.json()
            except Exception:
                raise AssertionError(
                    "Public selection returned invalid JSON; body withheld"
                ) from None
            if not isinstance(document, dict):
                raise AssertionError("Public selection document shape invalid; body withheld")
            documents[kind] = document
            record(completed.value, "validated", response.status)
        version = documents["races"].get("catalog_version")
        if (
            not isinstance(version, str)
            or any(doc.get("catalog_version") != version for doc in documents.values())
            or documents["races"].get("total") != len(expected_ids)
            or [item["race"]["id"] for item in documents["races"].get("items", [])] != expected_ids
            or [item["id"] for item in documents["map"].get("features", [])] != expected_ids
            or [item["race"]["id"] for item in documents["witness"].get("items", [])]
            != expected_ids[:1]
        ):
            raise AssertionError("Public selection IDs/version mismatch; bodies withheld")
        trace["versions_equal"] = True
        trace["api_finished_ms"] = round((time.monotonic() - started) * 1000, 2)
        trace["phase"] = "presentation"
        expect(page.locator(".result-count strong")).to_have_text(
            str(len(expected_ids)), timeout=15000
        )
        trace["phase"] = "ready"
    except Exception as error:
        trace["error_type"] = type(error).__name__
        trace["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
        # Host cache only: a blocked renderer must not block or replace this evidence.
        trace["camera"] = camera_diagnostic(page)
        raise AssertionError("Public month selection failed: " + json.dumps(trace)) from error
    finally:
        for event, callback in callbacks.items():
            page.remove_listener(event, callback)
        trace["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
        print("PUBLIC_MONTH_SELECTION_TIMING " + json.dumps(trace))


@pytest.mark.e2e
def test_compiled_signup_explicit_confirmation_login_and_late_401_keep_discovery(
    account_server, database
):
    origin, sent, app = account_server
    identity(database, "bob@example.test")
    with sync_playwright() as playwright:
        browser = launch(playwright)
        context = browser.new_context(timezone_id="Europe/Paris")
        page = context.new_page()
        prepare(page)
        errors, leaks, public = [], [], []
        page.on("pageerror", lambda error: errors.append(type(error).__name__))

        def audit(request):
            path = urlsplit(request.url).path
            if path in {"/api/v1/map", "/api/v1/races", "/api/v1/catalog/options"}:
                public.append(path)
            if urlsplit(request.url).netloc != urlsplit(origin).netloc:
                if any(
                    key in request.headers
                    for key in ("x-csrf-token", "x-account-proof", "authorization")
                ):
                    leaks.append("private-header-on-provider")

        page.on("request", audit)
        try:
            response = page.goto(origin)
            assert response.headers["x-frame-options"] == "DENY"
            assert response.headers["content-security-policy"] == "frame-ancestors 'none'"
            assert response.headers["referrer-policy"] == "no-referrer"
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            page.get_by_role("button", name="Mois", exact=True).click()
            page.get_by_label("Mois", exact=True).select_option("11")
            page.get_by_label("Route", exact=True).check()
            page.get_by_placeholder("Course, commune ou club…").fill("race-road-split")
            expect(page.locator(".result-count strong")).to_have_text("1")
            assert install_camera_diagnostic(page)
            page.get_by_role("button", name=re.compile("Summit")).click()
            wait_camera_pitch(page, 60)
            page.wait_for_function(
                "Number(document.querySelector('.map-canvas').dataset.elevation)>100", timeout=10000
            )
            page.locator(".maplibregl-ctrl-zoom-in").click()
            page.wait_for_function(
                "JSON.parse(document.querySelector('.map-canvas').dataset.camera).zoom===7.5"
            )
            page.get_by_role("button", name="Explorer les communes", exact=True).click()
            page.locator(".race-row").filter(has_text="race-road-split").click()
            expect(page.locator(".race-detail h2")).to_have_text("Course fictive race-road-split")
            before = camera(page)
            node = page.locator(".map-canvas").element_handle()
            public_before = len(public)
            account(page)
            page.get_by_role("button", name="Créer un compte", exact=True).click()
            page.get_by_label("Adresse email", exact=True).fill("alice@example.test")
            page.get_by_label("Nouveau mot de passe", exact=True).fill(PASSWORD)
            page.get_by_label("Confirmer le mot de passe", exact=True).fill(PASSWORD)
            page.get_by_role("button", name="Créer un compte", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(ACCEPTED_TEXT)
            confirmation_link = take_link(sent, "confirmation", origin)
            # Renvoi refused by cooldown still reports202 and does not invalidate the first proof.
            page.get_by_role("button", name="Renvoyer la confirmation", exact=True).click()
            page.get_by_label("Adresse email", exact=True).fill("alice@example.test")
            page.get_by_role("button", name="Renvoyer la confirmation", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(ACCEPTED_TEXT)
            assert app.extensions["auth"].drain(5) and sent.empty()
            page.keyboard.press("Escape")
            expect(page.locator("dialog.account-dialog")).not_to_be_visible()
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            proof_page = context.new_page()
            prepare(proof_page)
            posts = []
            proof_page.on("request", lambda req: posts.append(1) if req.method == "POST" else None)
            navigate_proof(proof_page, confirmation_link)
            expect(
                proof_page.get_by_role("button", name="Confirmer mon adresse", exact=True)
            ).to_be_enabled()
            assert not urlsplit(proof_page.url).fragment and posts == []
            proof_page.get_by_role("button", name="Confirmer mon adresse", exact=True).click()
            expect(proof_page.locator(".account-message")).to_contain_text("Adresse confirmée")
            expect(proof_page.locator(".account-context")).to_contain_text(
                "Vous n’êtes pas connecté"
            )
            proof_page.close()
            page.bring_to_front()
            account(page)
            sign_in(page, "alice@example.test", PASSWORD)
            page.get_by_role("button", name="Utiliser un autre compte").click()
            page.get_by_label("Adresse email", exact=True).fill("alice@example.test")
            page.get_by_label("Mot de passe", exact=True).fill("Wrong synthetic password")
            page.get_by_role("button", name="Se connecter", exact=True).click()
            expect(page.locator(".account-error[role=alert]")).to_contain_text(
                "compte déjà connecté est conservé"
            )
            expect(page.locator(".account-context")).to_contain_text("alice@example.test")
            screenshot(page, "dialog-desktop.png")
            # A passive response held despite abort, then released AFTER loginB succeeds.
            page.evaluate("""() => {
                const original = window.fetch;
                let hold = true;
                window.fetch = async (url, options) => {
                    if (hold && url === '/api/v1/me') {
                        hold = false;
                        const copy = {...options}; delete copy.signal;
                        await original(url, copy);
                        return new Promise(resolve => {
                            window.releaseOldAccountRead = () => resolve(new Response(
                                JSON.stringify({code:'authentication_failed'}),
                                {status:401,headers:{'Content-Type':'application/json'}}));
                        });
                    }
                    return original(url, options);
                };
                window.dispatchEvent(new Event('focus'));
            }""")
            page.wait_for_function("typeof window.releaseOldAccountRead==='function'")
            sign_in(page, "bob@example.test", PASSWORD)
            page.evaluate(
                "async()=>{window.releaseOldAccountRead(); await Promise.resolve(); "
                "await Promise.resolve();}"
            )
            expect(page.locator(".account-context")).to_contain_text("bob@example.test")
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            assert node.evaluate("node=>node===document.querySelector('.map-canvas')")
            assert_camera_unchanged(camera(page), before)
            expect(page.get_by_label("Mois", exact=True)).to_have_value("11")
            expect(page.get_by_label("Route", exact=True)).to_be_checked()
            expect(page.get_by_placeholder("Course, commune ou club…")).to_have_value(
                "race-road-split"
            )
            expect(page.locator(".race-detail h2")).to_have_text("Course fictive race-road-split")
            assert len(public) == public_before and errors == [] and leaks == []
            assert page.evaluate("localStorage.length===0 && sessionStorage.length===0")
        except Exception:
            try:
                screenshot(page, "dialog-desktop.png")
            except Exception:
                # Preserve the original bounded camera diagnostic if capture also stalls.
                pass
            raise
        finally:
            context.close()
            browser.close()


@pytest.mark.e2e
def test_mobile_forgot_reset_b_keeps_a_until_explicit_login_and_scroll_keyboard(
    account_server, database
):
    origin, sent, _ = account_server
    alice = identity(database, "alice@example.test")
    identity(database, "bob@example.test")
    new_password = "  Another exact password for B 2026!  "
    with sync_playwright() as playwright:
        browser = launch(playwright)
        context = browser.new_context(
            timezone_id="Europe/Paris", viewport={"width": 390, "height": 844}
        )
        page = context.new_page()
        prepare(page, mobile=True)
        try:
            page.goto(origin)
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            account(page)
            sign_in(page, "alice@example.test", PASSWORD)
            page.get_by_role("button", name="Mot de passe oublié", exact=True).click()
            page.get_by_label("Adresse email", exact=True).fill("bob@example.test")
            page.get_by_role("button", name="Mot de passe oublié", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(ACCEPTED_TEXT)
            reset_link = take_link(sent, "reset", origin)
            proof_page = context.new_page()
            prepare(proof_page, mobile=True)
            navigate_proof(proof_page, reset_link)
            expect(proof_page.get_by_label("Nouveau mot de passe", exact=True)).to_be_visible()
            assert not urlsplit(proof_page.url).fragment
            proof_page.get_by_label("Nouveau mot de passe", exact=True).fill(new_password)
            proof_page.get_by_label("Confirmer le mot de passe", exact=True).fill(new_password)
            button = proof_page.get_by_role(
                "button", name="Choisir un nouveau mot de passe", exact=True
            )
            button.scroll_into_view_if_needed()
            expect(button).to_be_visible()
            screenshot(proof_page, "reset-form-mobile.png")
            button.click()
            expect(proof_page.locator(".account-message")).to_contain_text(
                "ne vous connecte pas automatiquement"
            )
            expect(proof_page.locator(".account-context")).to_contain_text("alice@example.test")
            assert context.request.get(origin + "/api/v1/me").json()["account"]["id"] == alice
            screenshot(proof_page, "account-reset.png")
            sign_in(proof_page, "bob@example.test", new_password)
            # Hold all passive B profile replies until an A input is focused.
            page.evaluate("""() => {
                const original = window.fetch;
                window.pendingAccountRefreshes = [];
                window.fetch = async (url, options) => {
                    if (url === '/api/v1/me' && !options.headers['X-CSRF-Token']) {
                        const copy = {...options}; delete copy.signal;
                        const response = await original(url, copy);
                        return new Promise(resolve => window.pendingAccountRefreshes.push(
                            () => resolve(response)));
                    }
                    return original(url, options);
                };
                window.releaseAccountRefreshes = () => {
                    window.fetch = original;
                    window.pendingAccountRefreshes.splice(0).forEach(release => release());
                };
            }""")
            proof_page.keyboard.press("Escape")
            expect(proof_page.locator("dialog.account-dialog")).not_to_be_visible()
            page.bring_to_front()
            page.evaluate("window.dispatchEvent(new Event('focus'))")
            page.wait_for_function("window.pendingAccountRefreshes.length>0")
            page.get_by_label("Adresse email", exact=True).focus()
            page.evaluate("() => window.releaseAccountRefreshes()")
            expect(page.locator(".account-context")).to_contain_text("bob@example.test")
            page.wait_for_function(
                "document.querySelector('dialog').contains(document.activeElement)",
                timeout=5000,
            )
            expect(page.locator(".account-message")).to_have_count(0)
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            page.get_by_role("button", name="Compte", exact=True).focus()
            page.keyboard.press("Enter")
            expect(page.locator("dialog.account-dialog")).to_be_visible()
            focus_state = """() => ({
                tag: document.activeElement.tagName,
                inside: document.querySelector('dialog').contains(document.activeElement),
                open: document.querySelector('dialog').open
            })"""
            before_tab = page.evaluate(focus_state)
            page.keyboard.press("Tab")
            after_tab = page.evaluate(focus_state)
            assert after_tab["inside"], {"before_tab": before_tab, "after_tab": after_tab}
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
        except Exception:
            screenshot(page, "account-mobile.png")
            raise
        finally:
            context.close()
            browser.close()


@pytest.mark.e2e
@pytest.mark.parametrize("mobile", [False, True], ids=["desktop", "mobile390"])
def test_copy202_is_identical_without_delivery_promise_when_provider_fails_or_no_mail_is_admitted(
    account_server, monkeypatch, mobile
):
    origin, sent, app = account_server
    address = f"provider-failure-{urlsplit(origin).port}@example.test"
    runtime = app.extensions["auth"]
    attempted = threading.Event()
    calls = []

    def refuse_quota(message, operation_id):
        calls.append(True)
        attempted.set()
        raise EmailDeliveryError("quota_exceeded")

    monkeypatch.setattr(runtime.email_service()._provider, "send", refuse_quota)
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris")
        prepare(page, mobile=mobile)
        try:
            page.goto(origin)
            account(page)
            page.get_by_role("button", name="Créer un compte", exact=True).click()
            page.get_by_label("Adresse email", exact=True).fill(address)
            page.get_by_label("Nouveau mot de passe", exact=True).fill(PASSWORD)
            page.get_by_label("Confirmer le mot de passe", exact=True).fill(PASSWORD)
            page.get_by_role("button", name="Créer un compte", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(ACCEPTED_TEXT)
            assert attempted.wait(timeout=5) and runtime.drain(5)
            assert len(calls) == 1 and sent.empty()
            page.locator(".account-message").scroll_into_view_if_needed()
            expect(page.locator(".account-message")).to_be_visible()
            screenshot(page, "account-mobile.png" if mobile else "dialog-desktop.png")
            # Same account/cooldown refusal and unknown address get exactly the same UI copy.
            page.get_by_role("button", name="Renvoyer la confirmation", exact=True).click()
            page.get_by_label("Adresse email", exact=True).fill(address)
            page.get_by_role("button", name="Renvoyer la confirmation", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(ACCEPTED_TEXT)
            page.get_by_role("button", name="Mot de passe oublié", exact=True).click()
            page.get_by_label("Adresse email", exact=True).fill("unknown@example.test")
            page.get_by_role("button", name="Mot de passe oublié", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(ACCEPTED_TEXT)
            assert runtime.drain(5) and len(calls) == 1
            page.get_by_role(
                "button", name="Créer un compte", exact=True
            ).scroll_into_view_if_needed()
            expect(page.get_by_role("button", name="Créer un compte", exact=True)).to_be_visible()
        except Exception:
            screenshot(page, "account-mobile.png" if mobile else "dialog-desktop.png")
            raise
        finally:
            browser.close()


@pytest.mark.e2e
def test_season_scope_actions_map_two_accounts_outside_public_filters(
    admission_clock, account_server, database
):
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from raceatlas.models import SavedEntry

    origin, _, _ = account_server
    alice = identity(database, "alice@example.test")
    bob = identity(database, "bob@example.test")
    clock_start = admission_clock.now()
    read_statuses = {"alice": {}, "bob": {}}
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris")
        prepare(page)

        def observe_read(response):
            if urlsplit(response.url).path == "/api/v1/me":
                phase = "alice" if admission_clock.now() == clock_start else "bob"
                counts = read_statuses[phase]
                counts[str(response.status)] = counts.get(str(response.status), 0) + 1

        page.on("response", observe_read)
        try:
            page.goto(origin)
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            page.get_by_role("button", name="Mois", exact=True).click()
            page.get_by_label("Mois", exact=True).select_option("11")
            page.get_by_label("Route", exact=True).check()
            page.get_by_placeholder("Course, commune ou club…").fill("race-road-split")
            expect(page.locator(".result-count strong")).to_have_text("1", timeout=15000)
            assert install_camera_diagnostic(page)
            assert "snapshot" in camera_diagnostic(page)
            page.get_by_role("button", name=re.compile("Summit")).click()
            wait_camera_pitch(page, 60)
            page.wait_for_function(
                "Number(document.querySelector('.map-canvas').dataset.elevation)>100", timeout=10000
            )
            page.locator(".maplibregl-ctrl-zoom-in").click()
            page.wait_for_function(
                "JSON.parse(document.querySelector('.map-canvas').dataset.camera).zoom===7.5"
            )
            before = camera(page)
            node = page.locator(".map-canvas").element_handle()
            if not page.locator(".results-panel").is_visible():
                page.get_by_role("button", name="Explorer les communes", exact=True).click()
            page.locator(".race-row").filter(has_text="race-road-split").click()
            page.locator(".race-detail .scope").first.get_by_role(
                "button", name="Se connecter pour sauvegarder cette liste", exact=True
            ).click()
            sign_in(page, "alice@example.test", PASSWORD)
            with Session(database) as session:
                assert (
                    list(session.scalars(select(SavedEntry).where(SavedEntry.account_id == alice)))
                    == []
                )
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            one = page.locator('.scope-save[data-scope-id="scope-split-one"]')
            two = page.locator('.scope-save[data-scope-id="scope-split-two"]')
            one.get_by_label("Votre statut pour cette liste").select_option("planned")
            one.get_by_role("button", name="Sauvegarder cette liste", exact=True).click()
            expect(one.locator(".scope-saved")).to_have_text("Sauvegardée : Prévue")
            two.get_by_label("Votre statut pour cette liste").select_option("registered")
            two.get_by_role("button", name="Sauvegarder cette liste", exact=True).click()
            expect(two.locator(".scope-saved")).to_have_text("Sauvegardée : Inscrit")
            account(page)
            page.get_by_role("button", name="Ma saison", exact=True).click()
            expect(page.locator(".season-row")).to_have_count(2)
            page.keyboard.press("Escape")
            select_public_month(page, "1", [])
            account(page)
            page.get_by_role("button", name="Ma saison", exact=True).click()
            expect(page.locator(".season-row")).to_have_count(2)
            page.locator(".season-row").first.click()
            expect(page.locator(".season-detail .scope")).to_have_count(1)
            expect(
                page.locator('.season-detail .scope-save[data-scope-id="scope-split-one"]')
            ).to_be_visible()
            expect(
                page.locator('.season-detail .scope-save[data-scope-id="scope-split-two"]')
            ).to_have_count(0)
            selected = page.locator(".season-detail .scope-save")
            selected.get_by_label("Votre statut pour cette liste").select_option("completed")
            expect(selected.locator(".scope-saved")).to_have_text("Sauvegardée : Terminée")
            selected.get_by_role("button", name="Retirer cette sauvegarde", exact=True).click()
            expect(page.locator(".season-row")).to_have_count(1)
            expect(page.locator(".notifications-panel")).to_have_attribute("aria-busy", "false")
            expect(page.get_by_role("button", name="Utiliser un autre compte")).to_be_enabled()
            screenshot(page, "season-desktop.png")
            # Two fast automated account journeys exceed read20/minute. Model a
            # deliberate pause between phases; production admission and every
            # CSRF→GETme→operation attestation remain unchanged.
            admission_clock.advance(61)
            sign_in(page, "bob@example.test", PASSWORD)
            page.get_by_role("button", name="Ma saison", exact=True).click()
            expect(page.get_by_text("Votre saison est vide.", exact=False)).to_be_visible()
            page.keyboard.press("Escape")
            select_public_month(page, "11", ["race-road-split"])
            if not page.locator(".results-panel").is_visible():
                page.get_by_role("button", name="Explorer les communes", exact=True).click()
            page.locator(".race-row").filter(has_text="race-road-split").click()
            two = page.locator('.scope-save[data-scope-id="scope-split-two"]')
            expect(
                two.get_by_role("button", name="Sauvegarder cette liste", exact=True)
            ).to_be_visible()
            two.get_by_role("button", name="Sauvegarder cette liste", exact=True).click()
            expect(two.locator(".scope-saved")).to_have_text("Sauvegardée : Intéressé")
            with Session(database) as session:
                values = {
                    (row.account_id, row.scope_id): row.status
                    for row in session.scalars(select(SavedEntry))
                }
            assert values == {
                (alice, "scope-split-two"): "registered",
                (bob, "scope-split-two"): "interested",
            }
            assert node.evaluate("node=>node===document.querySelector('.map-canvas')")
            assert_camera_unchanged(camera(page), before)
            expect(page.get_by_label("Mois", exact=True)).to_have_value("11")
            expect(page.get_by_label("Route", exact=True)).to_be_checked()
            assert all("429" not in phase for phase in read_statuses.values())
            assert all(sum(phase.values()) <= 20 for phase in read_statuses.values())
        except Exception:
            try:
                screenshot(page, "season-desktop.png")
            except Exception:
                # Never replace the original transport/camera evidence with capture failure.
                pass
            raise
        finally:
            # Counts/statuses only: never record private URL queries, headers,
            # bodies, proof strings or account identifiers in this diagnostic.
            try:
                path = SHOTS.parent / "ops-n2b1-ci-browser-phases.json"
                path.write_text(
                    json.dumps(
                        {
                            "read_peer_limit": 20,
                            "virtual_pause_seconds": 61,
                            "read_statuses": read_statuses,
                        },
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )
            except OSError:
                pass
            browser.close()


@pytest.mark.e2e
def test_mobile_calendar_scopes_and_season_keep_month_and_private_scope(account_server, database):
    origin, _, _ = account_server
    identity(database, "alice@example.test")
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris")
        prepare(page, mobile=True)
        try:
            page.goto(origin)
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            node = page.locator(".map-canvas").element_handle()
            page.get_by_role("button", name="Calendrier", exact=True).click()
            expect(page.locator(".calendar-view")).to_have_attribute("aria-busy", "false")
            page.locator('td[data-date="2026-11-11"] .calendar-day').click()
            page.locator(".race-row").filter(has_text="race-road-split").click()
            first = page.locator(".race-detail .scope").first
            first.get_by_role(
                "button", name="Se connecter pour sauvegarder cette liste", exact=True
            ).scroll_into_view_if_needed()
            first.get_by_role(
                "button", name="Se connecter pour sauvegarder cette liste", exact=True
            ).click()
            sign_in(page, "alice@example.test", PASSWORD)
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            one = page.locator('.scope-save[data-scope-id="scope-split-one"]')
            one.get_by_role(
                "button", name="Sauvegarder cette liste", exact=True
            ).scroll_into_view_if_needed()
            one.get_by_role("button", name="Sauvegarder cette liste", exact=True).click()
            expect(one.locator(".scope-saved")).to_have_text("Sauvegardée : Intéressé")
            two = page.locator('.scope-save[data-scope-id="scope-split-two"]')
            two.get_by_label("Votre statut pour cette liste").scroll_into_view_if_needed()
            two.get_by_label("Votre statut pour cette liste").select_option("planned")
            two.get_by_role("button", name="Sauvegarder cette liste", exact=True).click()
            expect(two.locator(".scope-saved")).to_have_text("Sauvegardée : Prévue")
            page.get_by_role("button", name="Fermer les détails", exact=True).click()
            page.get_by_role("button", name="Mois suivant", exact=True).scroll_into_view_if_needed()
            page.get_by_role("button", name="Mois suivant", exact=True).click()
            expect(page.locator(".calendar-view")).to_have_attribute("aria-busy", "false")
            expect(page.get_by_role("heading", name="Décembre 2026", exact=True)).to_be_visible()
            account(page)
            page.get_by_role("button", name="Ma saison", exact=True).click()
            expect(page.locator(".season-row")).to_have_count(2)
            screenshot(page, "season-mobile.png")
            page.locator(".season-row").last.click()
            expect(page.locator(".season-detail .scope")).to_have_count(1)
            scope = page.locator('.season-detail .scope-save[data-scope-id="scope-split-two"]')
            scope.get_by_label("Votre statut pour cette liste").scroll_into_view_if_needed()
            scope.get_by_label("Votre statut pour cette liste").select_option("registered")
            expect(scope.locator(".scope-saved")).to_have_text("Sauvegardée : Inscrit")
            expect(
                scope.get_by_text("« Inscrit » est votre déclaration, non vérifiée par la FFC.")
            ).to_be_visible()
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            expect(page.get_by_role("heading", name="Décembre 2026", exact=True)).to_be_visible()
            assert node.evaluate("node=>node===document.querySelector('.map-canvas')")
        except Exception:
            screenshot(page, "season-mobile.png")
            raise
        finally:
            browser.close()


@pytest.mark.e2e
def test_season_two_cookie_devices_do_not_share_private_identity(account_server, database):
    from sqlalchemy.orm import Session

    from raceatlas.models import Account
    from raceatlas.planning import put_saved_entry

    origin, _, _ = account_server
    alice = identity(database, "alice@example.test")
    identity(database, "bob@example.test")
    with Session(database) as session, session.begin():
        put_saved_entry(session, session.get(Account, alice), "scope-split-one", "planned")
    with sync_playwright() as playwright:
        browser = launch(playwright)
        first = browser.new_context(timezone_id="Europe/Paris")
        second = browser.new_context(timezone_id="Europe/Paris")
        try:
            pages = [first.new_page(), second.new_page()]
            for page in pages:
                prepare(page)
                page.goto(origin)
                account(page)
                sign_in(page, "alice@example.test", PASSWORD)
                page.get_by_role("button", name="Ma saison", exact=True).click()
                expect(page.locator(".season-row")).to_have_count(1)
                expect(page.locator(".season-row")).to_contain_text("Prévue")
            sign_in(pages[1], "bob@example.test", PASSWORD)
            pages[1].get_by_role("button", name="Ma saison", exact=True).click()
            expect(pages[1].get_by_text("Votre saison est vide.", exact=False)).to_be_visible()
            pages[0].bring_to_front()
            pages[0].get_by_role("button", name="Actualiser ma saison", exact=True).click()
            expect(pages[0].locator(".account-context")).to_contain_text("alice@example.test")
            expect(pages[0].locator(".season-row")).to_have_count(1)
            expect(pages[0].locator(".season-row")).to_contain_text("Prévue")
        finally:
            first.close()
            second.close()
            browser.close()


@pytest.mark.e2e
def test_calendar_download_uses_whole_private_season_and_unknown_response_is_honest(
    account_server, database, tmp_path
):
    from icalendar import Calendar
    from sqlalchemy.orm import Session

    from raceatlas.models import Account
    from raceatlas.planning import put_saved_entry

    origin, _, _ = account_server
    alice = identity(database, "alice@example.test")
    with Session(database) as session, session.begin():
        actor = session.get(Account, alice)
        for scope, status in (
            ("scope-split-one", "planned"),
            ("scope-split-two", "registered"),
            ("scope-road-combined", "completed"),
            ("scope-gravel", "interested"),
        ):
            put_saved_entry(session, actor, scope, status)
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris", accept_downloads=True)
        prepare(page)
        try:
            page.goto(origin)
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            page.get_by_role("button", name="Mois", exact=True).click()
            page.get_by_label("Mois", exact=True).select_option("1")
            page.get_by_label("Route", exact=True).check()
            expect(page.locator(".result-count strong")).to_have_text("0", timeout=15000)
            node = page.locator(".map-canvas").element_handle()
            before = camera(page)
            account(page)
            sign_in(page, "alice@example.test", PASSWORD)
            page.get_by_role("button", name="Ma saison", exact=True).click()
            expect(page.locator(".season-row")).to_have_count(4)
            screenshot(page, "calendar-export-desktop.png")
            with page.expect_download() as downloaded:
                page.get_by_role(
                    "button", name="Exporter les Prévues et Inscrit (.ics)", exact=True
                ).click()
            download = downloaded.value
            assert download.suggested_filename == "raceatlas-planning.ics"
            destination = tmp_path / "planning.ics"
            download.save_as(destination)
            events = Calendar.from_ical(destination.read_bytes()).walk("VEVENT")
            assert len(events) == 2
            assert len({str(event["UID"]) for event in events}) == 2
            assert all("race-road-split" in str(event["SUMMARY"]) for event in events)
            assert all(event["DTEND"].dt > event["DTSTART"].dt for event in events)
            page.get_by_role("button", name="Sécurité du compte", exact=True).click()
            # A synthetically unexpected2xx must never fabricate logout success.
            calls = []

            def unexpected(route):
                calls.append(1)
                route.fulfill(status=202, content_type="application/json", body="{}")

            page.route("**/api/v1/auth/logout", unexpected)
            page.get_by_role("button", name="Se déconnecter", exact=True).click()
            expect(page.get_by_role("alert")).to_contain_text("n’est pas confirmé")
            expect(page.locator(".account-context")).to_contain_text("alice@example.test")
            assert len(calls) == 1
            page.unroute("**/api/v1/auth/logout", unexpected)
            committed = []

            def lose_committed_response(route):
                result = route.fetch()
                committed.append(result.status)
                route.abort("failed")

            page.route("**/api/v1/auth/logout", lose_committed_response)
            page.get_by_role("button", name="Se déconnecter", exact=True).click()
            expect(page.get_by_role("alert")).to_contain_text("n’est pas confirmé")
            expect(page.locator(".account-context")).to_contain_text("alice@example.test")
            assert committed == [204]
            page.unroute("**/api/v1/auth/logout", lose_committed_response)
            page.get_by_role("button", name="Vérifier le compte", exact=True).click()
            expect(page.locator(".account-context")).to_contain_text("n’êtes pas connecté")
            expect(page.locator(".account-message")).to_have_count(0)
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            expect(page.get_by_label("Mois", exact=True)).to_have_value("1")
            expect(page.get_by_label("Route", exact=True)).to_be_checked()
            assert node.evaluate("node=>node===document.querySelector('.map-canvas')")
            assert_camera_unchanged(camera(page), before)
        except Exception:
            screenshot(page, "calendar-export-desktop.png")
            raise
        finally:
            browser.close()


@pytest.mark.e2e
def test_mobile_security_reauth_devices_password_and_delete_isolate_private_data(
    account_server, database
):
    origin, _, _ = account_server
    identity(database, "alice@example.test")
    with sync_playwright() as playwright:
        browser = launch(playwright)
        first, second = (
            browser.new_context(timezone_id="Europe/Paris"),
            browser.new_context(timezone_id="Europe/Paris"),
        )
        page, device = first.new_page(), second.new_page()
        prepare(page, mobile=True)
        prepare(device)
        try:
            for target in (page, device):
                target.goto(origin)
                account(target)
                sign_in(target, "alice@example.test", PASSWORD)
            page.get_by_role("button", name="Sécurité du compte", exact=True).click()
            page.get_by_role("button", name="Se déconnecter", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(
                "Déconnexion effectuée sur cet appareil."
            )
            assert second.request.get(origin + "/api/v1/me").status == 200
            sign_in(page, "alice@example.test", PASSWORD)
            page.get_by_role("button", name="Sécurité du compte", exact=True).click()
            page.get_by_role("button", name="Déconnecter tous les appareils", exact=True).click()
            page.get_by_label("Mot de passe actuel", exact=True).fill("wrong synthetic")
            page.get_by_role("button", name="Déconnecter tous les appareils", exact=True).click()
            expect(page.get_by_role("alert")).to_contain_text("actuel est incorrect")
            expect(page.locator(".account-context")).to_contain_text("alice@example.test")
            expect(page.get_by_label("Mot de passe actuel", exact=True)).to_have_value("")
            page.get_by_label("Mot de passe actuel", exact=True).fill(PASSWORD)
            page.get_by_role("button", name="Déconnecter tous les appareils", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(
                "Déconnexion de tous vos appareils effectuée."
            )
            assert second.request.get(origin + "/api/v1/me").status == 401
        except Exception:
            screenshot(page, "security-mobile.png")
            raise
        finally:
            first.close()
            second.close()
            browser.close()


@pytest.mark.e2e
def test_mobile_password_and_delete_purge_only_owner(account_server, database):
    from datetime import datetime, timezone

    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from raceatlas.models import Account, CatalogState, PersonalCalendarEventStore, SavedEntry
    from raceatlas.planning import put_saved_entry

    origin, _, _ = account_server
    alice = identity(database, "alice@example.test")
    bob = identity(database, "bob@example.test")
    with Session(database) as session, session.begin():
        for user in (alice, bob):
            put_saved_entry(session, session.get(Account, user), "scope-split-one", "planned")
            session.add(
                PersonalCalendarEventStore(
                    account_id=user,
                    scope_id="scope-split-one",
                    fingerprint="a" * 64,
                    stamp=datetime.now(timezone.utc),
                    sequence=0,
                )
            )
        public = session.execute(select(CatalogState.epoch, CatalogState.revision)).one()
    with sync_playwright() as playwright:
        browser = launch(playwright)
        first, second = (
            browser.new_context(timezone_id="Europe/Paris"),
            browser.new_context(timezone_id="Europe/Paris"),
        )
        page, device = first.new_page(), second.new_page()
        prepare(page, mobile=True)
        prepare(device)
        try:
            new_password = " Replacement Exact Passphrase 2027 "
            for target in (page, device):
                target.goto(origin)
                account(target)
                sign_in(target, "alice@example.test", PASSWORD)
            page.get_by_role("button", name="Sécurité du compte", exact=True).click()
            page.get_by_role("button", name="Changer le mot de passe", exact=True).click()
            screenshot(page, "security-mobile.png")
            page.get_by_label("Mot de passe actuel", exact=True).fill(PASSWORD)
            page.get_by_label("Nouveau mot de passe", exact=True).fill(new_password)
            page.get_by_label("Confirmer le nouveau mot de passe", exact=True).fill(new_password)
            page.get_by_role("button", name="Changer le mot de passe", exact=True).click()
            expect(page.locator(".account-message")).to_contain_text("Mot de passe modifié")
            assert second.request.get(origin + "/api/v1/me").status == 401
            sign_in(page, "alice@example.test", new_password)
            page.get_by_role("button", name="Sécurité du compte", exact=True).click()
            page.get_by_role("button", name="Supprimer mon compte", exact=True).click()
            page.get_by_label("Mot de passe actuel", exact=True).fill(new_password)
            page.get_by_role("checkbox").check()
            page.get_by_role("button", name="Supprimer mon compte", exact=True).click()
            expect(page.locator(".account-message")).to_have_text(
                "Votre compte et ses données personnelles ont été supprimés."
            )
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()
            with Session(database) as session:
                assert session.get(Account, alice) is None
                assert session.get(Account, bob) is not None
                assert (
                    session.scalar(select(SavedEntry).where(SavedEntry.account_id == alice)) is None
                )
                assert session.get(PersonalCalendarEventStore, (alice, "scope-split-one")) is None
                assert session.get(PersonalCalendarEventStore, (bob, "scope-split-one")) is not None
                assert (
                    session.scalar(select(SavedEntry).where(SavedEntry.account_id == bob))
                    is not None
                )
                assert (
                    session.execute(select(CatalogState.epoch, CatalogState.revision)).one()
                    == public
                )
        except Exception:
            screenshot(page, "security-mobile.png")
            raise
        finally:
            first.close()
            second.close()
            browser.close()
