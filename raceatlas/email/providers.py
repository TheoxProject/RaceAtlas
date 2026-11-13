from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID, uuid4

import requests
import resend
from requests.adapters import HTTPAdapter
from resend.http_client import HTTPClient

from .config import (
    EmailConfigurationError,
    EmailDeliveryError,
    EmailInputError,
    EmailSettings,
    mailbox,
)
from .templates import SUBJECTS, EmailMessage

_SDK_LOCK = Lock()
MAX_RESPONSE_BYTES = 65536


def _validate_message(message, operation_id):
    if not isinstance(message, EmailMessage) or not isinstance(operation_id, UUID):
        raise EmailInputError()
    mailbox(message.recipient)
    if message.subject not in SUBJECTS.values():
        raise EmailInputError()
    for value, bound in [(message.html, 16384), (message.text, 4096)]:
        if not isinstance(value, str) or len(value) > bound or "\x00" in value:
            raise EmailInputError()
        invalid = False
        try:
            invalid = len(value.encode("utf-8")) > bound
        except UnicodeEncodeError:
            invalid = True
        if invalid:
            raise EmailInputError()


@dataclass(frozen=True)
class EmailReceipt:
    provider: str
    status: str
    message_id: str = field(repr=False)


class DevelopmentEmailProvider:
    kind = "development"

    def __init__(self, environment="local", capacity=20):
        if (
            environment not in {"local", "test"}
            or not isinstance(capacity, int)
            or not 1 <= capacity <= 100
        ):
            raise EmailConfigurationError()
        self._messages = deque(maxlen=capacity)
        self._lock = Lock()

    @property
    def messages(self):
        with self._lock:
            return tuple(self._messages)

    def send(self, message, operation_id):
        _validate_message(message, operation_id)
        with self._lock:
            self._messages.append(message)
        return EmailReceipt(self.kind, "simulated", str(uuid4()))


class BoundedResendHTTPClient(HTTPClient):
    """SDK transport, exact endpoint/TLS, no proxy/netrc/redirect/retry, bounded body."""

    def __init__(self, request_session=None):
        self._session = request_session if request_session is not None else requests.Session()
        self._session.trust_env = False
        self._session.mount("https://", HTTPAdapter(max_retries=0))

    def request(self, method, url, headers, json=None, files=None, data=None):
        if (
            method.lower() != "post"
            or url != "https://api.resend.com/emails"
            or files is not None
            or data is not None
        ):
            raise EmailDeliveryError()
        response = None
        failed = False
        result = None
        try:
            response = self._session.request(
                method="POST",
                url=url,
                headers=headers,
                json=json,
                verify=True,
                allow_redirects=False,
                timeout=(3.05, 5),
                stream=True,
            )
            if 300 <= response.status_code < 400:
                raise EmailDeliveryError()
            body = bytearray()
            for chunk in response.iter_content(chunk_size=4096):
                if not isinstance(chunk, bytes) or len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise EmailDeliveryError()
                body.extend(chunk)
            result = (
                bytes(body),
                response.status_code,
                {"content-type": response.headers.get("content-type", "")[:128]},
            )
        except (requests.RequestException, EmailDeliveryError):
            failed = True
        finally:
            if response is not None:
                response.close()
        if failed:
            raise EmailDeliveryError()
        return result


class ResendEmailProvider:
    kind = "resend"

    def __init__(self, settings, http_client=None):
        if not isinstance(settings, EmailSettings) or settings.provider != "resend":
            raise EmailConfigurationError()
        self._settings = settings
        self._client = http_client if http_client is not None else BoundedResendHTTPClient()
        if not isinstance(self._client, BoundedResendHTTPClient):
            raise EmailConfigurationError()

    def send(self, message, operation_id):
        _validate_message(message, operation_id)
        if not _SDK_LOCK.acquire(timeout=1):
            raise EmailDeliveryError("busy")
        previous = resend.api_key, resend.api_url, resend.default_http_client
        failed, result = None, None
        try:
            resend.api_key = self._settings.api_key
            resend.api_url = "https://api.resend.com"
            resend.default_http_client = self._client
            result = resend.Emails.send(
                {
                    "from": self._settings.sender,
                    "to": [message.recipient],
                    "subject": message.subject,
                    "html": message.html,
                    "text": message.text,
                },
                {"idempotency_key": str(operation_id)},
            )
        except Exception as error:
            code = getattr(error, "code", None)
            failed = "quota" if code == 429 else "rejected" if code == 403 else "delivery_failed"
        finally:
            resend.api_key, resend.api_url, resend.default_http_client = previous
            _SDK_LOCK.release()
        # Raise outside SDK exception handling: do not retain a secret-bearing context.
        if failed is not None:
            raise EmailDeliveryError(failed)
        identifier = result.get("id") if isinstance(result, dict) else None
        if not isinstance(identifier, str) or len(identifier) != 36:
            raise EmailDeliveryError()
        invalid = False
        try:
            normalized_id = str(UUID(identifier))
        except ValueError:
            invalid = True
        if invalid:
            raise EmailDeliveryError()
        return EmailReceipt(self.kind, "accepted", normalized_id)
