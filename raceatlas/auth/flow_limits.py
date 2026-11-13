"""Persistent reservations. Lock order: Account (if known), Budget, address quota."""

import hashlib
import hmac
import os
from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from raceatlas.auth import _now
from raceatlas.models import EmailAddressQuota, EmailBudget


class FlowConfigurationError(ValueError):
    def __init__(self):
        super().__init__("Invalid account flow configuration.")


@dataclass(frozen=True)
class FlowPolicy:
    rate_key: bytes = field(repr=False)
    cooldown_seconds: int = 60
    per_hour: int = 3
    per_day: int = 80
    per_month: int = 2400
    capacity: int = 4096

    def __post_init__(self):
        if not isinstance(self.rate_key, bytes) or not 32 <= len(self.rate_key) <= 1024:
            raise FlowConfigurationError()
        for value, low, high in [
            (self.cooldown_seconds, 0, 3600),
            (self.per_hour, 1, 100),
            (self.per_day, 1, 80),
            (self.per_month, 1, 2400),
            (self.capacity, 1, 4096),
        ]:
            if type(value) is not int or not low <= value <= high:
                raise FlowConfigurationError()

    @classmethod
    def from_environment(cls, environ=None):
        values = os.environ if environ is None else environ
        key = values.get("AUTH_RATE_KEY", "")
        invalid = False
        try:
            raw = key.encode("utf-8") if isinstance(key, str) else b""
        except UnicodeEncodeError:
            invalid = True
        if invalid:
            raise FlowConfigurationError()
        return cls(raw)


def admit(session, email, purpose, policy, *, wants_send):
    """Always commit normal refusals too. No account may be locked after this call."""
    now = _now(session)
    day, month = now.date(), now.date().replace(day=1)
    session.execute(
        insert(EmailBudget)
        .values(
            id=1,
            day=day,
            month=month,
            day_count=0,
            month_count=0,
        )
        .on_conflict_do_nothing(index_elements=[EmailBudget.id])
    )
    budget = session.scalar(
        select(EmailBudget)
        .where(EmailBudget.id == 1)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    # Time is read after waiting for the serialization lock, never client supplied.
    now = _now(session)
    day, month = now.date(), now.date().replace(day=1)
    if budget.day != day:
        budget.day, budget.day_count = day, 0
    if budget.month != month:
        budget.month, budget.month_count = month, 0
    expired = (
        select(EmailAddressQuota.address_digest, EmailAddressQuota.purpose)
        .where(EmailAddressQuota.expires_at <= now)
        .order_by(EmailAddressQuota.expires_at)
        .limit(32)
    )
    # Bound work and storage. All writers hold the singleton, including purge.
    for digest, old_purpose in session.execute(expired):
        session.execute(
            delete(EmailAddressQuota).where(
                EmailAddressQuota.address_digest == digest,
                EmailAddressQuota.purpose == old_purpose,
            )
        )
    digest = hmac.new(policy.rate_key, email.encode("ascii"), hashlib.sha256).hexdigest()
    quota = session.get(EmailAddressQuota, (digest, purpose), populate_existing=True)
    if wants_send and (
        budget.day_count >= policy.per_day or budget.month_count >= policy.per_month
    ):
        return False
    if quota is not None:
        if now < quota.last_admitted_at + timedelta(seconds=policy.cooldown_seconds):
            return False
        recent = [stamp for stamp in quota.admissions if stamp > now - timedelta(hours=1)]
        if len(recent) >= policy.per_hour:
            return False
    else:
        if session.scalar(select(func.count()).select_from(EmailAddressQuota)) >= policy.capacity:
            return False
        quota = EmailAddressQuota(
            address_digest=digest, purpose=purpose, window_started_at=now, admitted=0, admissions=[]
        )
        session.add(quota)
        recent = []
    quota.admissions = recent + [now]
    quota.admitted = len(quota.admissions)
    quota.window_started_at = quota.admissions[0]
    quota.last_admitted_at, quota.expires_at = now, now + timedelta(hours=2)
    if wants_send:
        budget.day_count += 1
        budget.month_count += 1
    session.flush()
    return True
