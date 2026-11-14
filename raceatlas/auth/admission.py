"""Independent short admission COMMIT ends before any Account transaction starts."""

import hashlib
import hmac
import ipaddress
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from raceatlas.auth import _now
from raceatlas.models import AuthAdmissionBucket, AuthAdmissionState

from .http_settings import AuthConfigurationError


@dataclass(frozen=True)
class AdmissionPolicy:
    per_global: int = 60
    per_peer: int = 20
    per_address: int = 5
    capacity: int = 4096

    def __post_init__(self):
        if any(
            type(value) is not int or not 1 <= value <= upper
            for value, upper in [
                (self.per_global, 100),
                (self.per_peer, 100),
                (self.per_address, 100),
                (self.capacity, 4096),
            ]
        ):
            raise AuthConfigurationError()


def key_digest(key, namespace, action, value):
    return hmac.new(
        key, f"http-admission:v1:{namespace}:{action}:{value}".encode("utf-8"), hashlib.sha256
    ).hexdigest()


def admit_http(engine, rate_key, action, peer, *, address=None, policy=None):
    policy = AdmissionPolicy() if policy is None else policy
    if (
        not isinstance(engine, Engine)
        or not isinstance(policy, AdmissionPolicy)
        or not isinstance(action, str)
        or action
        not in {
            "csrf",
            "login",
            "request",
            "proof",
            "sensitive",
            "read",
            "planning",
        }
    ):
        raise AuthConfigurationError()
    if not isinstance(peer, str) or len(peer) > 45:
        return False
    try:
        peer = ipaddress.ip_address(peer).compressed
    except (ValueError, TypeError):
        return False
    if (
        not isinstance(rate_key, bytes)
        or len(rate_key) < 32
        or address is not None
        and (
            not isinstance(address, str)
            or len(address) > 254
            or any(not c.isprintable() for c in address)
        )
    ):
        raise AuthConfigurationError()
    specs = [("global", "all", "all", policy.per_global), ("peer", action, peer, policy.per_peer)]
    if address is not None:
        specs.append(("address", action, address, policy.per_address))
    # Own this short transaction: callers must not already hold Account locks.
    with Session(engine) as session, session.begin():
        if session.connection().connection.driver_connection.autocommit:
            raise AuthConfigurationError()
        session.execute(select(func.set_config("statement_timeout", "3000", True)))
        session.execute(select(func.set_config("lock_timeout", "1000", True)))
        session.execute(
            insert(AuthAdmissionState)
            .values(id=1, accepted=0, denied=0)
            .on_conflict_do_nothing(index_elements=[AuthAdmissionState.id])
        )
        state = session.scalar(
            select(AuthAdmissionState).where(AuthAdmissionState.id == 1).with_for_update()
        )
        now = _now(session)
        expired = session.scalars(
            select(AuthAdmissionBucket)
            .where(AuthAdmissionBucket.expires_at <= now)
            .order_by(AuthAdmissionBucket.expires_at)
            .limit(32)
        ).all()
        for row in expired:
            session.delete(row)
        session.flush()
        size = session.scalar(select(func.count()).select_from(AuthAdmissionBucket))
        changes = []
        for namespace, scope, value, limit in specs:
            digest = key_digest(rate_key, namespace, scope, value)
            row = session.get(AuthAdmissionBucket, (namespace, digest))
            recent = (
                []
                if row is None
                else [stamp for stamp in row.admissions if stamp > now - timedelta(minutes=1)]
            )
            if len(recent) >= limit or row is None and size >= policy.capacity:
                state.denied += 1
                return False
            if row is None:
                size += 1
            changes.append((namespace, digest, row, recent))
        for namespace, digest, row, recent in changes:
            if row is None:
                row = AuthAdmissionBucket(namespace=namespace, key_digest=digest)
                session.add(row)
            row.admissions, row.expires_at = recent + [now], now + timedelta(hours=1)
        state.accepted += 1
    return True
