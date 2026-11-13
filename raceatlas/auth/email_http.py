"""Proof-driven email HTTP flows. No provider work or ORM survives in a request job."""

from flask import jsonify, request
from sqlalchemy import func, select

from raceatlas.email.config import EmailConfigurationError, EmailInputError, mailbox
from raceatlas.planning import PlanningError, normalize_email

from .admission import admit_http
from .csrf import AuthRequestError, account_proof, parse_json, verify_request
from .flows import (
    AccountFlowSession,
    InvalidProof,
    complete_password_reset,
    confirm_email,
    request_password_reset,
    request_registration,
    resend_confirmation,
)
from .new_passwords import validate_new_password
from .passwords import dummy_verify


def register_email_routes(app, blueprint, runtime, error_handler):
    def invalid_proof(_error):
        return error_handler(AuthRequestError("invalid_proof", 400))

    blueprint.errorhandler(InvalidProof)(invalid_proof)

    def prepare(fields):
        verify_request(runtime.settings, request)
        return parse_json(request, fields)

    def email(value):
        try:
            return mailbox(normalize_email(value))
        except (EmailInputError, PlanningError):
            raise AuthRequestError("invalid_request", 400) from None

    def admission(kind, address=None):
        if not admit_http(
            app.extensions["database"],
            runtime.settings.rate_policy.rate_key,
            kind,
            request.remote_addr,
            address=address,
            policy=runtime.admission_policy,
        ):
            raise AuthRequestError("limited", 429)

    def transaction(action):
        with AccountFlowSession(app.extensions["database"]) as session:
            session.execute(select(func.set_config("statement_timeout", "3000", True)))
            session.execute(select(func.set_config("lock_timeout", "1000", True)))
            result = action(session)
            session.commit()
        return result

    def mail_request(action, address, *, password=None):
        with runtime.operation():
            admission("request", address)
            try:
                runtime.email_service()  # Validate shared service before Account lookup, no worker.
            except EmailConfigurationError:
                raise AuthRequestError("unavailable", 503) from None
            result = transaction(action)
            if password is not None and result.intent is None:
                dummy_verify(password)  # No double KDF: B2 hashes iff intent exists.
            if result.intent is not None:
                runtime.enqueue_email(app.extensions["database"], result.intent)
        # Queue capacity, business refusal, absent account and provider failures all match.
        return jsonify(status="accepted"), 202

    @blueprint.post("/register")
    def register():
        body = prepare({"email", "password"})
        address = email(body["email"])
        validate_new_password(body["password"])
        return mail_request(
            lambda session: request_registration(
                session, address, body["password"], policy=runtime.settings.rate_policy
            ),
            address,
            password=body["password"],
        )

    @blueprint.post("/confirmation/resend")
    def resend():
        body = prepare({"email"})
        address = email(body["email"])
        return mail_request(
            lambda session: resend_confirmation(
                session, address, policy=runtime.settings.rate_policy
            ),
            address,
        )

    @blueprint.post("/password-reset/request")
    def forgot():
        body = prepare({"email"})
        address = email(body["email"])
        return mail_request(
            lambda session: request_password_reset(
                session, address, policy=runtime.settings.rate_policy
            ),
            address,
        )

    @blueprint.post("/confirmation/complete")
    def confirm():
        prepare(set())
        proof = account_proof(request)
        with runtime.operation():
            admission("proof")
            transaction(lambda session: confirm_email(session, proof))
        return app.response_class(status=204)

    @blueprint.post("/password-reset/complete")
    def reset():
        body = prepare({"new_password"})
        proof = account_proof(request)
        validate_new_password(body["new_password"])
        with runtime.operation():
            admission("proof")
            transaction(
                lambda session: complete_password_reset(session, proof, body["new_password"])
            )
        return app.response_class(status=204)
