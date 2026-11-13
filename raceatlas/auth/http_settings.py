"""Auth configuration derives only from final Flask app.config, never request metadata."""

from dataclasses import dataclass, field
from secrets import compare_digest
from urllib.parse import urlsplit

from raceatlas.email.config import EmailConfigurationError, EmailSettings, load_settings

from .flow_limits import FlowConfigurationError, FlowPolicy


class AuthConfigurationError(ValueError):
    def __init__(self):
        super().__init__("Account features unavailable.")


def _secret(value):
    invalid = False
    try:
        raw = value.encode("utf-8") if isinstance(value, str) else b""
    except UnicodeEncodeError:
        invalid = True
    if invalid or not 32 <= len(raw) <= 1024:
        raise AuthConfigurationError()
    return raw


@dataclass(frozen=True, repr=False)
class AuthSettings:
    environment: str
    origin: str
    secure: bool
    csrf_key: bytes = field(repr=False)
    rate_policy: FlowPolicy = field(repr=False)
    email_settings: EmailSettings = field(repr=False)

    @property
    def session_cookie(self):
        return "__Host-raceatlas-session" if self.secure else "raceatlas_session_dev"

    @property
    def csrf_cookie(self):
        return "__Host-raceatlas-csrf" if self.secure else "raceatlas_csrf_dev"


def load_auth_settings(config):
    enabled = config.get("AUTH_ENABLED", False)
    if enabled is False or enabled == "false":
        return None
    if enabled is not True and enabled != "true":
        raise AuthConfigurationError()
    csrf = _secret(config.get("AUTH_CSRF_KEY"))
    rate = _secret(config.get("AUTH_RATE_KEY"))
    if compare_digest(csrf, rate):
        raise AuthConfigurationError()
    values = {
        key: config.get(key, "")
        for key in (
            "APP_BASE_URL",
            "EMAIL_PROVIDER",
            "RESEND_API_KEY",
            "EMAIL_FROM",
            "EMAIL_VERIFIED_DOMAIN",
            "EMAIL_SEND_AUTHORIZED",
            "EMAIL_TRACKING_DISABLED",
        )
    }
    values["RACEATLAS_ENV"] = config.get("ENVIRONMENT")
    if not values["EMAIL_PROVIDER"]:
        values["EMAIL_PROVIDER"] = "development"
    try:
        email_settings = load_settings(values)
        policy = FlowPolicy(rate)
    except (EmailConfigurationError, FlowConfigurationError):
        raise AuthConfigurationError() from None
    origin = email_settings.app_base_url.removesuffix("/")
    return AuthSettings(
        config["ENVIRONMENT"],
        origin,
        urlsplit(origin).scheme == "https",
        csrf,
        policy,
        email_settings,
    )
