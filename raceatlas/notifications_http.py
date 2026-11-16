"""Private notification pages and snapshot-wide acknowledgement."""

from flask import Blueprint, request
from sqlalchemy import func, select

from raceatlas import auth
from raceatlas.auth.admission import admit_http
from raceatlas.auth.csrf import AuthRequestError, check_origin, parse_json, verify_request
from raceatlas.auth.errors import AuthenticationFailed
from raceatlas.auth.flows import AccountFlowSession
from raceatlas.notifications_api import (
    NotificationQueryError,
    mark_all_notifications_read,
    parse_query,
    read_notifications,
)
from raceatlas.planning_snapshot import PlanningLimitError, PlanningLimits


def register_notification_routes(app, runtime, error_handler):
    blueprint = Blueprint("private_notifications", __name__, url_prefix="/api/v1/me/notifications")
    blueprint.errorhandler(AuthRequestError)(error_handler)
    app.extensions["notification_limits"] = PlanningLimits()

    @blueprint.before_request
    def available():
        # The auth/planning boundary rejects every query string. This additive
        # endpoint instead validates only its own limit/cursor below, before SQL.
        if runtime.settings is None:
            raise AuthRequestError("unavailable", 503)

    @blueprint.errorhandler(AuthenticationFailed)
    def unauthorized(_error):
        return error_handler(AuthRequestError("authentication_failed", 401))

    @blueprint.errorhandler(NotificationQueryError)
    def invalid_query(_error):
        return error_handler(AuthRequestError("invalid_request", 400))

    @blueprint.errorhandler(PlanningLimitError)
    def oversized(_error):
        return error_handler(AuthRequestError("selection_limit", 413))

    @blueprint.after_request
    def no_store(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    def run(action):
        with runtime.operation():
            settings = runtime.settings
            if not admit_http(
                app.extensions["database"],
                settings.rate_policy.rate_key,
                "notifications",
                request.remote_addr,
                policy=runtime.admission_policy,
            ):
                raise AuthRequestError("limited", 429)
            with AccountFlowSession(app.extensions["database"]) as session:
                session.execute(select(func.set_config("statement_timeout", "3000", True)))
                session.execute(select(func.set_config("lock_timeout", "1000", True)))
                actor = auth.resolve_session(session, request.cookies.get(settings.session_cookie))
                result = action(session, actor)
                session.commit()
        return result

    @blueprint.get("")
    def listing():
        if "X-CSRF-Token" in request.headers:
            verify_request(runtime.settings, request, mutation=False)
        else:
            check_origin(runtime.settings, request, mutation=False)
        if set(request.args) - {"limit", "cursor"} or any(
            len(request.args.getlist(key)) != 1 for key in request.args
        ):
            raise NotificationQueryError()
        limit, _claim = parse_query(request.args.get("limit", 50), request.args.get("cursor"))
        data = run(
            lambda session, actor: read_notifications(
                session,
                actor,
                cursor_key=runtime.settings.csrf_key,
                limit=limit,
                cursor=request.args.get("cursor"),
                limits=app.extensions["notification_limits"],
            )
        )
        return app.response_class(data, mimetype="application/json")

    @blueprint.post("/read-all")
    def acknowledge():
        verify_request(runtime.settings, request)
        if request.args:
            raise NotificationQueryError()
        parse_json(request, set())
        run(mark_all_notifications_read)
        return app.response_class(status=204)

    app.register_blueprint(blueprint)
