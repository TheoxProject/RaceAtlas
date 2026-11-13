"""CSRF is not a bearer: proof is bound to an HttpOnly nonce and session cookie."""

import hashlib
import hmac
import json
import re
import secrets
import time

from werkzeug.exceptions import RequestEntityTooLarge

LIFETIME = 1800
_NONCE = re.compile(r"[A-Za-z0-9_-]{43}\Z", re.ASCII)
_COOKIE = re.compile(r"([A-Za-z0-9_-]{43})\.([0-9]{1,11})\.([a-f0-9]{64})\Z", re.ASCII)
_MAC = re.compile(r"[a-f0-9]{64}\Z", re.ASCII)


class AuthRequestError(ValueError):
    def __init__(self, code="forbidden", status=403):
        self.code, self.status = code, status
        super().__init__("Account request rejected.")


def _mac(key, value):
    return hmac.new(key, value.encode("ascii"), hashlib.sha256).hexdigest()


def valid_cookie(settings, value, now=None):
    if not isinstance(value, str) or len(value) > 120:
        return False
    match = _COOKIE.fullmatch(value)
    if match is None:
        return False
    nonce, expires, signature = match.groups()
    now = int(time.time()) if now is None else now
    return now < int(expires) <= now + LIFETIME and hmac.compare_digest(
        signature, _mac(settings.csrf_key, f"cookie:v1:{nonce}.{expires}")
    )


def proof(settings, cookie, session_cookie):
    # A malformed/huge bearer is never trusted or hashed without a bound.
    bearer = (
        session_cookie
        if isinstance(session_cookie, str) and _NONCE.fullmatch(session_cookie)
        else ""
    )
    binding = hashlib.sha256(bearer.encode("ascii")).hexdigest()
    return _mac(settings.csrf_key, f"proof:v1:{cookie}:{binding}")


def issue(settings, cookie=None, session_cookie=None, *, now=None):
    now = int(time.time()) if now is None else now
    fresh = not valid_cookie(settings, cookie, now)
    if fresh:
        nonce, expires = secrets.token_urlsafe(32), str(now + LIFETIME)
        stem = f"{nonce}.{expires}"
        cookie = f"{stem}.{_mac(settings.csrf_key, 'cookie:v1:' + stem)}"
    return proof(settings, cookie, session_cookie), cookie, fresh


def check_origin(settings, request, *, mutation):
    origin = request.headers.get("Origin")
    if (mutation and origin != settings.origin) or (
        origin is not None and origin != settings.origin
    ):
        raise AuthRequestError()
    if request.headers.get("Sec-Fetch-Site") not in {None, "same-origin", "none"}:
        raise AuthRequestError()


def verify_request(settings, request):
    check_origin(settings, request, mutation=True)
    cookie = request.cookies.get(settings.csrf_cookie)
    token = request.headers.get("X-CSRF-Token", "")
    if (
        not isinstance(token, str)
        or not _MAC.fullmatch(token)
        or not valid_cookie(settings, cookie)
        or not hmac.compare_digest(
            token, proof(settings, cookie, request.cookies.get(settings.session_cookie))
        )
    ):
        raise AuthRequestError()


def set_cookie(response, settings, value):
    response.set_cookie(
        settings.csrf_cookie,
        value,
        max_age=LIFETIME,
        secure=settings.secure,
        httponly=True,
        samesite="Lax",
        path="/",
    )


def parse_json(request, fields):
    """Strict object schema, no duplicate/NaN/UTF8 coercion; passwords remain exact."""
    if request.mimetype != "application/json":
        raise AuthRequestError("invalid_request", 400)
    request.max_content_length = 8192
    raw = request.get_data(cache=False)
    # Werkzeug may return a body cached before max_content_length was installed.
    if len(raw) > 8192:
        raise RequestEntityTooLarge()

    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    def constant(value):
        raise ValueError()

    try:
        body = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise AuthRequestError("invalid_request", 400) from None
    if (
        not isinstance(body, dict)
        or set(body) != set(fields)
        or any(not isinstance(value, str) for value in body.values())
    ):
        raise AuthRequestError("invalid_request", 400)
    return body


def account_proof(request):
    value = request.headers.get("X-Account-Proof", "")
    if not isinstance(value, str) or not _NONCE.fullmatch(value):
        raise AuthRequestError("invalid_proof", 400)
    return value
