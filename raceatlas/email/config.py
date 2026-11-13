import ipaddress
import re
from dataclasses import dataclass, field
from email.utils import parseaddr
from urllib.parse import urlsplit, urlunsplit


class EmailConfigurationError(ValueError):
    def __init__(self):
        super().__init__("Invalid email configuration.")


class EmailInputError(ValueError):
    def __init__(self):
        super().__init__("Invalid email request.")


class EmailDeliveryError(RuntimeError):
    def __init__(self, code="delivery_failed"):
        self.code = code
        super().__init__("Email delivery failed.")


def domain(value):
    if not isinstance(value, str) or len(value) > 253 or not value.isascii():
        raise EmailConfigurationError()
    value = value.lower()
    labels = value.split(".")
    if len(labels) < 2 or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels
    ):
        raise EmailConfigurationError()
    return value


def mailbox(value):
    if (
        not isinstance(value, str)
        or not 3 <= len(value) <= 254
        or not value.isascii()
        or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+", value)
    ):
        raise EmailInputError()
    local, host = value.rsplit("@", 1)
    if len(local) > 64:
        raise EmailInputError()
    try:
        domain(host)
    except EmailConfigurationError:
        raise EmailInputError() from None
    return value


def canonical_base(value, environment):
    if (
        not isinstance(environment, str)
        or environment not in {"local", "test", "production"}
        or not isinstance(value, str)
        or not 1 <= len(value) <= 512
        or not value.isascii()
        or any(character.isspace() or not character.isprintable() for character in value)
        or any(character in value for character in "\\%?#")
    ):
        raise EmailConfigurationError()
    try:
        parsed = urlsplit(value)
        host, port = parsed.hostname, parsed.port
    except ValueError:
        raise EmailConfigurationError() from None
    if (
        parsed.scheme not in {"http", "https"}
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.netloc.endswith(":")
        or port is not None
        and not 1 <= port <= 65535
    ):
        raise EmailConfigurationError()
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    loopback = host == "localhost" or address is not None and address.is_loopback
    if parsed.scheme == "http" and (environment == "production" or not loopback):
        raise EmailConfigurationError()
    if not loopback and address is None:
        domain(host)
    netloc = f"[{host}]" if address is not None and address.version == 6 else host
    if port is not None and port != (443 if parsed.scheme == "https" else 80):
        netloc += f":{port}"
    return urlunsplit((parsed.scheme, netloc, "/", "", ""))


@dataclass(frozen=True, repr=False)
class EmailSettings:
    environment: str
    provider: str
    app_base_url: str
    api_key: str = field(default="", repr=False)
    sender: str = field(default="", repr=False)
    verified_domain: str = field(default="", repr=False)
    send_authorized: bool = False
    tracking_disabled: bool = False

    def __post_init__(self):
        object.__setattr__(
            self, "app_base_url", canonical_base(self.app_base_url, self.environment)
        )
        if self.provider == "development" and self.environment in {"local", "test"}:
            return
        if self.provider != "resend":
            raise EmailConfigurationError()
        verified = _verified_sender(
            self.api_key,
            self.sender,
            self.verified_domain,
            self.send_authorized,
            self.tracking_disabled,
        )
        object.__setattr__(self, "verified_domain", verified)


def load_settings(environ):
    environment = environ.get("RACEATLAS_ENV", "local")
    provider = environ.get("EMAIL_PROVIDER", "development")
    return EmailSettings(
        environment,
        provider,
        environ.get("APP_BASE_URL", ""),
        environ.get("RESEND_API_KEY", ""),
        environ.get("EMAIL_FROM", ""),
        environ.get("EMAIL_VERIFIED_DOMAIN", ""),
        environ.get("EMAIL_SEND_AUTHORIZED") == "true",
        environ.get("EMAIL_TRACKING_DISABLED") == "true",
    )


def _verified_sender(key, sender, verified_domain, send_authorized, tracking_disabled):
    if (
        not isinstance(key, str)
        or not re.fullmatch(r"re_[A-Za-z0-9_-]{8,253}", key)
        or not isinstance(sender, str)
        or len(sender) > 320
        or any(not character.isprintable() for character in sender)
    ):
        raise EmailConfigurationError()
    name, address = parseaddr(sender)
    try:
        mailbox(address)
    except EmailInputError:
        raise EmailConfigurationError() from None
    if sender != (f"{name} <{address}>" if name else address):
        raise EmailConfigurationError()
    verified = domain(verified_domain)
    if (
        address.rsplit("@", 1)[1].lower() != verified
        or verified == "resend.dev"
        or verified.endswith(".resend.dev")
        or send_authorized is not True
        or tracking_disabled is not True
    ):
        raise EmailConfigurationError()
    return verified
