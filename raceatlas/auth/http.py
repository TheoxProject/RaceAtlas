"""HTTP boundary foundation. Session and email flow endpoints are subsequent C milestones."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import BoundedSemaphore
from time import time as wall_time

from flask import Blueprint, g, jsonify, request

from .admission import AdmissionPolicy, admit_http
from .csrf import AuthRequestError, check_origin, issue, set_cookie
from .http_settings import AuthConfigurationError, load_auth_settings


@dataclass(repr=False)
class AuthRuntime:
    settings: object
    state: str
    admission_policy: AdmissionPolicy = field(default_factory=AdmissionPolicy)
    slots: object = field(default_factory=lambda: BoundedSemaphore(2), repr=False)

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

    app.register_blueprint(blueprint)
