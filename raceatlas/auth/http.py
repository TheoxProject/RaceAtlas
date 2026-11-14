"""HTTP boundary foundation. Session and email flow endpoints are subsequent C milestones."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import BoundedSemaphore, Lock
from time import time as wall_time

from flask import Blueprint, g, jsonify, request

from raceatlas.email import EmailService
from raceatlas.email.providers import DevelopmentEmailProvider, ResendEmailProvider
from raceatlas.planning_http import register_planning_routes

from .admission import AdmissionPolicy, admit_http
from .csrf import AuthRequestError, check_origin, issue, set_cookie
from .dispatch import DispatcherUnavailable, open_channel
from .email_http import register_email_routes
from .http_settings import AuthConfigurationError, load_auth_settings
from .sessions_http import register_session_routes


@dataclass(repr=False)
class AuthRuntime:
    settings: object
    state: str
    admission_policy: AdmissionPolicy = field(default_factory=AdmissionPolicy)
    slots: object = field(default_factory=lambda: BoundedSemaphore(2), repr=False)
    _service: object = field(default=None, init=False, repr=False)
    _channel: object = field(default=None, init=False, repr=False)
    _email_closed: bool = field(default=False, init=False, repr=False)
    _email_lock: object = field(default_factory=Lock, init=False, repr=False)

    def email_service(self):
        with self._email_lock:
            if self._service is None:
                settings = self.settings.email_settings
                provider = (
                    DevelopmentEmailProvider(settings.environment)
                    if settings.provider == "development"
                    else ResendEmailProvider(settings)
                )
                self._service = EmailService(settings, provider)
            return self._service

    def enqueue_email(self, engine, intent):
        service = self.email_service()
        with self._email_lock:
            if self._email_closed:
                return False
            if self._channel is None:
                try:
                    self._channel = open_channel(engine, service)
                except DispatcherUnavailable:
                    return False
            channel = self._channel
        return channel.enqueue(intent)

    def cancel_pending(self, account_id):
        with self._email_lock:
            channel = self._channel
        return 0 if channel is None else channel.cancel_pending(account_id)

    def drain(self, timeout=5):
        with self._email_lock:
            channel = self._channel
        return True if channel is None else channel.drain(timeout)

    def close(self, timeout=1):
        with self._email_lock:
            self._email_closed = True
            channel = self._channel
        return True if channel is None else channel.close(timeout)

    @contextmanager
    def operation(self):
        if not self.slots.acquire(blocking=False):
            raise AuthRequestError("limited", 429)
        try:
            yield
        finally:
            self.slots.release()


def init_auth(app):
    try:
        settings = load_auth_settings(app.config)
        runtime = AuthRuntime(settings, "disabled" if settings is None else "available")
    except AuthConfigurationError:
        runtime = AuthRuntime(None, "unavailable")
        app.logger.error("Account features unavailable.")
    app.extensions["auth"] = runtime
    blueprint = Blueprint("account_auth", __name__, url_prefix="/api/v1/auth")

    @blueprint.errorhandler(AuthRequestError)
    def account_error(error):
        return jsonify(
            code=error.code,
            message="Requête de compte non disponible.",
            fields=[],
            request_id=g.request_id,
        ), error.status

    @blueprint.before_request
    def account_boundary():
        if runtime.settings is None:
            raise AuthRequestError("unavailable", 503)
        if request.args:
            raise AuthRequestError("invalid_request", 400)

    @blueprint.get("/csrf")
    def csrf_token():
        settings = runtime.settings
        check_origin(settings, request, mutation=False)
        with runtime.operation():
            if not admit_http(
                app.extensions["database"],
                settings.rate_policy.rate_key,
                "csrf",
                request.remote_addr,
                policy=runtime.admission_policy,
            ):
                raise AuthRequestError("limited", 429)
            now = int(wall_time())
            token, cookie, fresh = issue(
                settings,
                request.cookies.get(settings.csrf_cookie),
                request.cookies.get(settings.session_cookie),
                now=now,
            )
        response = jsonify(csrf_token=token, expires_in=int(cookie.split(".")[1]) - now)
        if fresh:
            set_cookie(response, settings, cookie)
        return response

    register_session_routes(app, blueprint, runtime, account_boundary, account_error)
    register_email_routes(app, blueprint, runtime, account_error)
    register_planning_routes(app, runtime, account_boundary, account_error)
    app.register_blueprint(blueprint)
