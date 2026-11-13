"""Cookie-only session routes; transactions close before publishing response cookies."""

import hashlib
import hmac
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

import raceatlas.auth as auth
from raceatlas.models import EmailAddressQuota, EmailBudget
from raceatlas.planning import PlanningError, delete_account, normalize_email

from .admission import admit_http
from .csrf import AuthRequestError, check_origin, issue, parse_json, set_cookie, verify_request
from .errors import (
    AuthenticationFailed,
    AuthenticationUnavailable,
    InvalidPassword,
    ReauthenticationFailed,
)
from .flow_limits import FlowConfigurationError
from .flows import AccountFlowSession
from .new_passwords import validate_new_password


def _clear_cookies(response, settings):
    for name in (settings.session_cookie, settings.csrf_cookie):
        response.delete_cookie(
            name, path="/", secure=settings.secure, httponly=True, samesite="Lax"
        )
    return response


def _purge_account(session, account, rate_key):
    # Account lock already held by reauthentication. No other Account acquired here.
    digest = hmac.new(
        rate_key, account.email_normalized.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    now = auth._now(session)
    session.execute(
        insert(EmailBudget)
        .values(id=1, day=now.date(), month=now.date().replace(day=1), day_count=0, month_count=0)
        .on_conflict_do_nothing(index_elements=[EmailBudget.id])
    )
    session.scalar(
        select(EmailBudget)
        .where(EmailBudget.id == 1)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    session.execute(delete(EmailAddressQuota).where(EmailAddressQuota.address_digest == digest))
    delete_account(session, account)
    session.flush()


def register_session_routes(app, blueprint, runtime, boundary, error_handler):
    members = Blueprint("account_members", __name__)
    members.before_request(boundary)
    members.errorhandler(AuthRequestError)(error_handler)

    def failed_auth(_error):
        # A late passive 401 must not erase a fresh login from another tab.
        # Stale cookies remain replaceable through GET csrf -> fresh login.
        return error_handler(AuthRequestError("authentication_failed", 401))

    def failed_reauth(_error):
        return error_handler(AuthRequestError("reauthentication_failed", 403))

    def invalid_password(_error):
        return error_handler(AuthRequestError("invalid_password", 400))

    def unavailable(_error):
        return error_handler(AuthRequestError("unavailable", 503))

    def private_headers(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    for target in (blueprint, members):
        target.errorhandler(AuthenticationFailed)(failed_auth)
        target.errorhandler(ReauthenticationFailed)(failed_reauth)
        target.errorhandler(InvalidPassword)(invalid_password)
        target.errorhandler(AuthenticationUnavailable)(unavailable)
        target.errorhandler(FlowConfigurationError)(unavailable)
        target.after_request(private_headers)

    def prepare(fields):
        verify_request(runtime.settings, request)
        return parse_json(request, fields)

    def run(action, kind, *, address=None):
        settings = runtime.settings
        with runtime.operation():
            if not admit_http(
                app.extensions["database"],
                settings.rate_policy.rate_key,
                kind,
                request.remote_addr,
                address=address,
                policy=runtime.admission_policy,
            ):
                raise AuthRequestError("limited", 429)
            with AccountFlowSession(app.extensions["database"]) as session:
                session.execute(select(func.set_config("statement_timeout", "3000", True)))
                session.execute(select(func.set_config("lock_timeout", "1000", True)))
                result = action(session)
                session.commit()
            return result

    def token():
        # Authorization (including preview Basic) is never an account identity.
        return request.cookies.get(runtime.settings.session_cookie)

    @blueprint.post("/login", endpoint="login")
    def login_session():
        body = prepare({"email", "password"})
        try:
            address = normalize_email(body["email"])
        except PlanningError:
            address = "invalid-address"

        def authenticate(session):
            grant = auth.authenticate(session, body["email"], body["password"])
            account = auth.resolve_session(session, grant.token)
            return grant, {"id": account.id, "email": account.email_normalized}

        grant, profile = run(authenticate, "login", address=address)
        settings = runtime.settings
        csrf, cookie, _ = issue(settings, session_cookie=grant.token)
        response = jsonify(account=profile, csrf_token=csrf, expires_in=1800)
        remaining = max(
            0, min(604800, int((grant.expires_at - datetime.now(timezone.utc)).total_seconds()))
        )
        response.set_cookie(
            settings.session_cookie,
            grant.token,
            max_age=remaining,
            expires=grant.expires_at,
            path="/",
            secure=settings.secure,
            httponly=True,
            samesite="Lax",
        )
        set_cookie(response, settings, cookie)
        return response

    @members.get("/api/v1/me")
    def me():
        check_origin(runtime.settings, request, mutation=False)

        def current(session):
            account = auth.resolve_session(session, token())
            return {"id": account.id, "email": account.email_normalized}

        return jsonify(account=run(current, "read"))

    @blueprint.post("/logout")
    def logout_session():
        prepare(set())
        run(lambda session: auth.logout(session, token()), "sensitive")
        return _clear_cookies(app.response_class(status=204), runtime.settings)

    @blueprint.post("/logout-all")
    def logout_all():
        body = prepare({"current_password"})

        def revoke(session):
            auth.reauthenticate(session, token(), body["current_password"])
            auth.logout_all(session, token())

        run(revoke, "sensitive")
        return _clear_cookies(app.response_class(status=204), runtime.settings)

    @blueprint.post("/password/change")
    def change_password():
        body = prepare({"current_password", "new_password"})

        def change(session):
            auth.resolve_session(session, token())
            validate_new_password(body["new_password"])
            auth.change_password(session, token(), body["current_password"], body["new_password"])

        run(change, "sensitive")
        return _clear_cookies(app.response_class(status=204), runtime.settings)

    @members.delete("/api/v1/me")
    def delete_me():
        body = prepare({"current_password"})

        def remove(session):
            account = auth.reauthenticate(session, token(), body["current_password"])
            _purge_account(session, account, runtime.settings.rate_policy.rate_key)

        run(remove, "sensitive")
        return _clear_cookies(app.response_class(status=204), runtime.settings)

    app.register_blueprint(members)
