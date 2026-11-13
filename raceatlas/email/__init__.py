"""Central email boundary; no business registration/reset or network fallback."""

import os
import re
from uuid import UUID, uuid4

from .config import EmailConfigurationError, EmailInputError, EmailSettings, load_settings
from .providers import DevelopmentEmailProvider, ResendEmailProvider
from .templates import render_message


class EmailService:
    def __init__(self, settings, provider):
        if (
            not isinstance(settings, EmailSettings)
            or not isinstance(provider, (DevelopmentEmailProvider, ResendEmailProvider))
            or settings.provider != provider.kind
            or settings.provider == "development"
            and settings.environment not in {"local", "test"}
        ):
            raise EmailConfigurationError()
        if isinstance(provider, ResendEmailProvider) and provider._settings != settings:
            raise EmailConfigurationError()
        self._settings = settings
        self._provider = provider

    @classmethod
    def from_environment(cls, environ=None, *, http_client=None):
        settings = load_settings(os.environ if environ is None else environ)
        provider = (
            DevelopmentEmailProvider(settings.environment)
            if settings.provider == "development"
            else ResendEmailProvider(settings, http_client)
        )
        return cls(settings, provider)

    def render(self, purpose, recipient, token):
        return render_message(self._settings.app_base_url, purpose, recipient, token)

    def _send(self, purpose, recipient, token, operation_id):
        if operation_id is None:
            operation_id = uuid4()
        if not isinstance(operation_id, UUID):
            if not isinstance(operation_id, str) or not re.fullmatch(
                r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}", operation_id
            ):
                raise EmailInputError()
            operation_id = UUID(operation_id)
        message = self.render(purpose, recipient, token)
        return self._provider.send(message, operation_id)

    def send_confirmation(self, recipient, token, *, operation_id=None):
        return self._send("confirmation", recipient, token, operation_id)

    def send_password_reset(self, recipient, token, *, operation_id=None):
        return self._send("reset", recipient, token, operation_id)
