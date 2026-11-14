"""Cookie-authenticated private saved scopes and static personal ICS."""

from flask import Blueprint, request
from sqlalchemy import func, select

from raceatlas import auth
from raceatlas.auth.admission import admit_http
from raceatlas.auth.csrf import AuthRequestError, check_origin, parse_json, verify_request
from raceatlas.auth.errors import AuthenticationFailed
from raceatlas.auth.flows import AccountFlowSession
from raceatlas.calendar_store import materialize_calendar
from raceatlas.models import SavedEntry
from raceatlas.planning import (
    PlanningError,
    _actor_id,
    _status,
    _target_id,
    delete_saved_entry,
    put_saved_entry,
    update_saved_entry,
)
from raceatlas.planning_snapshot import (
    PlanningLimitError,
    PlanningLimits,
    encode_personal,
    snapshot_documents,
)


def register_planning_routes(app, runtime, boundary, error_handler):
    blueprint = Blueprint("private_planning", __name__, url_prefix="/api/v1/me")
    blueprint.before_request(boundary)
    blueprint.errorhandler(AuthRequestError)(error_handler)
    app.extensions["planning_limits"] = PlanningLimits()

    @blueprint.errorhandler(AuthenticationFailed)
    def unauthorized(_error):
        return error_handler(AuthRequestError("authentication_failed", 401))

    @blueprint.errorhandler(PlanningError)
    def domain_error(error):
        return error_handler(
            AuthRequestError(
                "not_found" if error.code == "not_found" else "invalid_status",
                404 if error.code == "not_found" else 400,
            )
        )

    @blueprint.errorhandler(PlanningLimitError)
    def limit_error(_error):
        return error_handler(AuthRequestError("selection_limit", 413))

    @blueprint.after_request
    def private_response(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    def prepare(fields=None):
        if fields is None:
            check_origin(runtime.settings, request, mutation=False)
            return None
        verify_request(runtime.settings, request)
        return parse_json(request, fields)

    def run(action):
        settings = runtime.settings
        with runtime.operation():
            if not admit_http(
                app.extensions["database"],
                settings.rate_policy.rate_key,
                "planning",
                request.remote_addr,
                policy=runtime.admission_policy,
            ):
                raise AuthRequestError("limited", 429)
            with AccountFlowSession(app.extensions["database"]) as session:
                session.execute(select(func.set_config("statement_timeout", "3000", True)))
                session.execute(select(func.set_config("lock_timeout", "1000", True)))
                actor = auth.resolve_session(session, request.cookies.get(settings.session_cookie))
                result = action(session, actor, app.extensions["planning_limits"])
                session.commit()
        return result

    def response(data):
        return app.response_class(data, mimetype="application/json")

    @blueprint.get("/saved-entries")
    def saved_entries():
        prepare()

        def read(session, actor, limits):
            return encode_personal(
                {"items": snapshot_documents(session, actor, limits=limits)}, limits
            )

        return response(run(read))

    @blueprint.put("/saved-entries/by-scope/<scope_id>")
    def put(scope_id):
        body = prepare({"status"})

        def save(session, actor, limits):
            target = _target_id(scope_id)
            status = _status(body["status"])
            account_id = _actor_id(session, actor)
            existing = session.scalar(
                select(SavedEntry.id).where(
                    SavedEntry.account_id == account_id, SavedEntry.scope_id == target
                )
            )
            if (
                existing is None
                and session.scalar(
                    select(func.count())
                    .select_from(SavedEntry)
                    .where(SavedEntry.account_id == account_id)
                )
                >= limits.saved_entries
            ):
                raise PlanningLimitError()
            entry = put_saved_entry(session, actor, target, status)
            return encode_personal(
                {"item": snapshot_documents(session, actor, entry_id=entry.id, limits=limits)[0]},
                limits,
            )

        return response(run(save))

    @blueprint.patch("/saved-entries/<entry_id>")
    def patch(entry_id):
        body = prepare({"status"})

        def update(session, actor, limits):
            entry = update_saved_entry(session, actor, entry_id, body["status"])
            return encode_personal(
                {"item": snapshot_documents(session, actor, entry_id=entry.id, limits=limits)[0]},
                limits,
            )

        return response(run(update))

    @blueprint.delete("/saved-entries/<entry_id>")
    def delete(entry_id):
        prepare(set())
        run(lambda session, actor, limits: delete_saved_entry(session, actor, entry_id))
        return app.response_class(status=204)

    @blueprint.get("/calendar.ics")
    def calendar():
        prepare()
        data = run(materialize_calendar)
        result = app.response_class(data, content_type="text/calendar; charset=utf-8")
        result.headers["Content-Disposition"] = 'attachment; filename="raceatlas-planning.ics"'
        return result

    app.register_blueprint(blueprint)
