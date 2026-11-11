"""Public continuation tokens, bound to canonical filter and catalogue snapshot.

No authorization information is carried here. The checksum detects corrupted tokens;
the database snapshot and filter binding are always checked independently on every page.
"""

import base64
import hashlib
import json
import re

from .validation import CatalogError, parse_json


def encode_cursor(version, filter_hash, offset):
    body = {"v": 1, "catalog": version, "filter": filter_hash, "offset": offset}
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("ascii")
    envelope = payload + b"." + hashlib.sha256(payload).hexdigest().encode("ascii")
    return base64.urlsafe_b64encode(envelope).decode("ascii").rstrip("=")


def decode_cursor(token, version, filter_hash):
    if token is None:
        return 0
    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
            raise ValueError
        decoded = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
        payload, checksum = decoded.rsplit(b".", 1)
        if hashlib.sha256(payload).hexdigest().encode("ascii") != checksum:
            raise ValueError
        body = parse_json(payload.decode("ascii"), max_length=2048)
        if (
            not isinstance(body, dict)
            or set(body) != {"v", "catalog", "filter", "offset"}
            or type(body["v"]) is not int
            or body["v"] != 1
            or type(body["offset"]) is not int
            or not 1 <= body["offset"] <= 2**31 - 1
            or not isinstance(body["catalog"], str)
            or body["filter"] != filter_hash
        ):
            raise ValueError
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise CatalogError(fields=["cursor"]) from None
    if body["catalog"] != version:
        raise CatalogError("stale_cursor", fields=["cursor"], status=409)
    return body["offset"]
