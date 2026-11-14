"""Compiled React -> real Flask/PostgreSQL, synthetic memory email only."""

import re
import threading
from pathlib import Path
from queue import Queue
from urllib.parse import urlsplit

import pytest
import requests
from map_support import camera, intercept_map, launch, set_civil_date
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
            screenshot(page, "dialog-desktop.png")
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
