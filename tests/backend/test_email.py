import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from html.parser import HTMLParser
from threading import Event
from uuid import uuid4

import pytest
import requests
import resend

from raceatlas.email import EmailService
from raceatlas.email.config import (
    EmailConfigurationError,
    EmailDeliveryError,
    EmailInputError,
    EmailSettings,
    canonical_base,
    load_settings,
)
from raceatlas.email.providers import (
    _SDK_LOCK,
    MAX_RESPONSE_BYTES,
    BoundedResendHTTPClient,
    DevelopmentEmailProvider,
)

TOKEN = "syntheticToken" + "A" * 29
KEY = "re_synthetic_key_never_real"
RECIPIENT = "synthetic-recipient@example.test"
PROVIDER_ID = "e06ce732-106d-4d2f-95fc-b214bf4eed65"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden in all email tests")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)


def environment(**patch):
    return {"RACEATLAS_ENV": "test", "APP_BASE_URL": "https://site.example.test", **patch}


def resend_environment(**patch):
    return environment(
        EMAIL_PROVIDER="resend",
        RESEND_API_KEY=KEY,
        EMAIL_FROM="RaceAtlas <sender@mail.example.test>",
        EMAIL_VERIFIED_DOMAIN="mail.example.test",
        EMAIL_SEND_AUTHORIZED="true",
        EMAIL_TRACKING_DISABLED="true",
        **patch,
    )


class FakeResponse:
    def __init__(self, *, status=200, body=None, content_type="application/json", chunks=None):
        self.status_code = status
        self.headers = {"content-type": content_type}
        self.body = json.dumps({"id": PROVIDER_ID}).encode() if body is None else body
        self.chunks = chunks
        self.closed = False

    def iter_content(self, chunk_size):
        assert chunk_size == 4096
        yield from self.chunks if self.chunks is not None else [self.body]

    def close(self):
        self.closed = True


class FakeRequestsSession:
    def __init__(self, response=None, failure=None, callback=None):
        self.response = response or FakeResponse()
        self.failure, self.callback = failure, callback
        self.calls = []
        self.trust_env = True
        self.adapters = {}

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter

    def request(self, **kwargs):
        self.calls.append(kwargs)
        if self.callback:
            self.callback(kwargs)
        if self.failure:
            raise self.failure
        return self.response


def sdk_service(fake, **patch):
    return EmailService.from_environment(
        resend_environment(**patch), http_client=BoundedResendHTTPClient(fake)
    )


@pytest.mark.parametrize(
    "purpose,button,expiry,key,subject",
    [
        (
            "confirmation",
            "Confirmer mon adresse e-mail",
            "24 heures",
            "confirm-email",
            "Confirmez votre adresse e-mail — RaceAtlas",
        ),
        (
            "reset",
            "Réinitialiser mon mot de passe",
            "30 minutes",
            "reset-password",
            "Réinitialisez votre mot de passe — RaceAtlas",
        ),
    ],
)
def test_french_models_and_root_fragments_are_static_private_and_resource_free(
    purpose, button, expiry, key, subject
):
    service = EmailService.from_environment(environment())
    message = service.render(purpose, RECIPIENT, TOKEN)
    link = f"https://site.example.test/#{key}={TOKEN}"
    assert message.subject == subject
    assert button in message.html and button in message.text
    assert expiry in message.html and expiry in message.text
    assert link in message.html and link in message.text
    assert "ignorez cet e-mail" in message.html and "ignorez cet e-mail" in message.text
    assert "#111F37" in message.html and "#F97316" in message.html
    assert all(
        value not in repr(message) for value in [TOKEN, RECIPIENT, message.html, message.text]
    )

    class Inspector(HTMLParser):
        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            assert tag not in {"script", "img", "iframe", "link"}
            assert "src" not in values and "url(" not in values.get("style", "")
            if "href" in values:
                assert values["href"] == link

    Inspector().feed(message.html)


def test_development_default_is_bounded_and_never_delivers_or_uses_secrets():
    settings = load_settings(environment(RESEND_API_KEY=KEY))
    provider = DevelopmentEmailProvider("test", capacity=2)
    service = EmailService(settings, provider)
    for _ in range(3):
        receipt = service.send_confirmation(RECIPIENT, TOKEN)
        assert receipt.provider == "development" and receipt.status == "simulated"
    assert len(provider.messages) == 2
    assert RECIPIENT not in repr(provider.messages)
    with pytest.raises(EmailConfigurationError):
        DevelopmentEmailProvider("production")


@pytest.mark.parametrize(
    "base,env,expected",
    [
        ("https://EXAMPLE.test:443", "production", "https://example.test/"),
        ("http://localhost:5000/", "local", "http://localhost:5000/"),
        ("http://127.0.0.1:5000", "test", "http://127.0.0.1:5000/"),
        ("http://[::1]:5000", "test", "http://[::1]:5000/"),
    ],
)
def test_canonical_origins_only(base, env, expected):
    assert canonical_base(base, env) == expected


@pytest.mark.parametrize(
    "base",
    [
        "",
        "//evil.test",
        "javascript:alert(1)",
        "http://site.example.test",
        "http://127.0.0.1.evil.test",
        "https://user@site.test",
        "https://site.test/path",
        "https://site.test?",
        "https://site.test#",
        "https://site.test:0",
        "https://site.test:",
        "https://site.test:65536",
        "https://site.test\\evil",
        "https://site.test/%2f",
        "https://site.test\n",
        "https://site.test\x00",
        "https://\ud800.test",
        None,
        {},
    ],
)
def test_unsafe_base_is_generic_without_host_or_forwarded_fallback(base):
    with pytest.raises(EmailConfigurationError, match="^Invalid email configuration\\.$"):
        EmailService.from_environment(
            environment(APP_BASE_URL=base, HOST="safe.test", HTTP_HOST="safe.test")
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"RACEATLAS_ENV": "production"},
        {"EMAIL_PROVIDER": "unknown"},
        {"EMAIL_PROVIDER": "resend"},
        {"RACEATLAS_ENV": []},
    ],
)
def test_provider_fail_closed(patch):
    with pytest.raises(EmailConfigurationError):
        EmailService.from_environment(environment(**patch))


@pytest.mark.parametrize(
    "patch",
    [
        {"RESEND_API_KEY": ""},
        {"RESEND_API_KEY": "re_bad\r\nkey"},
        {"EMAIL_FROM": ""},
        {"EMAIL_FROM": "sender@other.test"},
        {"EMAIL_FROM": "sender@mail.example.test\r\nBcc:x@test.test"},
        {"EMAIL_VERIFIED_DOMAIN": ""},
        {"EMAIL_SEND_AUTHORIZED": "false"},
        {"EMAIL_TRACKING_DISABLED": "false"},
        {"EMAIL_FROM": "sender@resend.dev", "EMAIL_VERIFIED_DOMAIN": "resend.dev"},
    ],
)
def test_resend_requires_all_operator_attestations_and_exact_sender_domain(patch):
    configured = resend_environment()
    configured.update(patch)
    with pytest.raises(EmailConfigurationError, match="^Invalid email configuration\\.$"):
        EmailService.from_environment(configured)
    with pytest.raises(EmailConfigurationError):
        EmailSettings("production", "resend", "https://site.test")


@pytest.mark.parametrize(
    "recipient,token",
    [
        ("bad\r\nBcc:other@test.test", TOKEN),
        ("<script>@test.test", TOKEN),
        (RECIPIENT, 'bad" onclick=alert(1)'),
        (RECIPIENT, "A" * 44),
        (RECIPIENT, "A" * 42 + "\ud800"),
        (RECIPIENT, None),
    ],
)
def test_message_input_cannot_inject_header_html_or_token(recipient, token):
    service = EmailService.from_environment(environment())
    with pytest.raises(EmailInputError, match="^Invalid email request\\.$"):
        service.send_confirmation(recipient, token)


def test_direct_provider_also_bounds_message_memory_and_idempotency():
    provider = DevelopmentEmailProvider("test")
    message = EmailService.from_environment(environment()).render("confirmation", RECIPIENT, TOKEN)
    for invalid in [
        replace(message, html="x" * 16385),
        replace(message, text="\ud800"),
        replace(message, text="x" * 4097),
    ]:
        with pytest.raises(EmailInputError):
            provider.send(invalid, uuid4())
    with pytest.raises(EmailInputError):
        provider.send(message, RECIPIENT)
    assert provider.messages == ()


def test_real_sdk_send_uses_exact_isolated_transport_and_opaque_idempotency(monkeypatch):
    fake = FakeRequestsSession()
    service = sdk_service(fake)
    previous = resend.api_key, resend.api_url, resend.default_http_client
    monkeypatch.setenv("RESEND_API_URL", "http://evil.test")
    operation = uuid4()
    receipt = service.send_confirmation(RECIPIENT, TOKEN, operation_id=operation)
    assert (receipt.provider, receipt.status, receipt.message_id) == (
        "resend",
        "accepted",
        PROVIDER_ID,
    )
    assert (resend.api_key, resend.api_url, resend.default_http_client) == previous
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["method"] == "POST" and call["url"] == "https://api.resend.com/emails"
    assert call["verify"] is True and call["allow_redirects"] is False and call["stream"] is True
    assert call["timeout"] == (3.05, 5)
    assert call["headers"]["Authorization"] == f"Bearer {KEY}"
    assert call["headers"]["Idempotency-Key"] == str(operation)
    assert call["headers"]["User-Agent"].startswith("resend-python:")
    assert (
        call["json"]["to"] == [RECIPIENT]
        and call["json"]["from"] == "RaceAtlas <sender@mail.example.test>"
    )
    assert "#confirm-email=" in call["json"]["html"]
    assert fake.response.closed and fake.trust_env is False
    assert fake.adapters["https://"].max_retries.total == 0
    assert all(value not in repr(receipt) for value in [KEY, TOKEN, RECIPIENT, PROVIDER_ID])


@pytest.mark.parametrize(
    "status,code",
    [(403, "rejected"), (429, "quota"), (500, "delivery_failed"), (503, "delivery_failed")],
)
def test_sdk_http_failures_are_masked_no_retry_and_restore_globals(status, code, caplog):
    fake = FakeRequestsSession(
        FakeResponse(
            status=status,
            body=json.dumps(
                {"message": f"{KEY} {RECIPIENT} {TOKEN}", "name": "application_error"}
            ).encode(),
        )
    )
    service = sdk_service(fake)
    previous = resend.api_key, resend.api_url, resend.default_http_client
    with pytest.raises(EmailDeliveryError, match="^Email delivery failed\\.$") as caught:
        service.send_password_reset(RECIPIENT, TOKEN)
    assert caught.value.code == code and caught.value.__context__ is None
    assert (resend.api_key, resend.api_url, resend.default_http_client) == previous
    assert len(fake.calls) == 1 and fake.response.closed
    assert all(
        value not in str(caught.value) + repr(caught.value) + caplog.text
        for value in [KEY, TOKEN, RECIPIENT]
    )


@pytest.mark.parametrize(
    "response,failure",
    [
        (None, requests.Timeout(f"{KEY} {TOKEN} {RECIPIENT}")),
        (None, requests.ConnectionError(f"{KEY} {TOKEN}")),
        (FakeResponse(status=302), None),
        (FakeResponse(body=b"not json"), None),
        (FakeResponse(body=b"null"), None),
        (FakeResponse(body=b"[]"), None),
        (FakeResponse(body=b'{"id":"not-an-id"}'), None),
        (FakeResponse(content_type="text/html"), None),
        (FakeResponse(chunks=[b"x" * MAX_RESPONSE_BYTES, b"x"]), None),
        (FakeResponse(body=b"\xff"), None),
    ],
)
def test_bad_sdk_network_or_response_is_bounded_and_generic(response, failure):
    fake = FakeRequestsSession(response, failure)
    previous = resend.api_key, resend.api_url, resend.default_http_client
    with pytest.raises(EmailDeliveryError, match="^Email delivery failed\\.$") as caught:
        sdk_service(fake).send_confirmation(RECIPIENT, TOKEN)
    assert caught.value.__context__ is None
    assert len(fake.calls) == 1
    assert (resend.api_key, resend.api_url, resend.default_http_client) == previous
    if failure is None:
        assert fake.response.closed


@pytest.mark.parametrize(
    "method,url",
    [
        ("GET", "https://api.resend.com/emails"),
        ("POST", "http://api.resend.com/emails"),
        ("POST", "https://evil.test/emails"),
        ("POST", "https://api.resend.com/emails/"),
        ("POST", "https://api.resend.com/emails?x=1"),
    ],
)
def test_transport_refuses_any_other_endpoint_before_network(method, url):
    fake = FakeRequestsSession()
    with pytest.raises(EmailDeliveryError):
        BoundedResendHTTPClient(fake).request(method, url, {})
    assert fake.calls == []


def test_multiple_provider_instances_cannot_cross_keys_and_restore_preexisting_sdk_globals():
    entered, release = Event(), Event()

    def pause(kwargs):
        entered.set()
        assert release.wait(3)

    first, second = FakeRequestsSession(callback=pause), FakeRequestsSession()
    one = sdk_service(first)
    two_env = resend_environment()
    two_env.update(
        RESEND_API_KEY="re_other_synthetic_key",
        EMAIL_FROM="Other <sender@other.test>",
        EMAIL_VERIFIED_DOMAIN="other.test",
    )
    two = EmailService.from_environment(two_env, http_client=BoundedResendHTTPClient(second))
    previous = resend.api_key, resend.api_url, resend.default_http_client
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(one.send_confirmation, RECIPIENT, TOKEN)
        try:
            assert entered.wait(3)
            b = pool.submit(two.send_password_reset, RECIPIENT, TOKEN)
        finally:
            release.set()
        assert a.result(timeout=5).status == b.result(timeout=5).status == "accepted"
    assert first.calls[0]["headers"]["Authorization"] == f"Bearer {KEY}"
    assert second.calls[0]["headers"]["Authorization"] == "Bearer re_other_synthetic_key"
    assert first.calls[0]["json"]["from"] != second.calls[0]["json"]["from"]
    assert (resend.api_key, resend.api_url, resend.default_http_client) == previous


def test_sdk_lock_wait_is_bounded_and_does_not_pollute_state():
    fake = FakeRequestsSession()
    service = sdk_service(fake)
    previous = resend.api_key, resend.api_url, resend.default_http_client
    with _SDK_LOCK:
        with pytest.raises(EmailDeliveryError) as caught:
            service.send_confirmation(RECIPIENT, TOKEN)
    assert caught.value.code == "busy" and fake.calls == []
    assert (resend.api_key, resend.api_url, resend.default_http_client) == previous
    assert service.send_confirmation(RECIPIENT, TOKEN).status == "accepted"
