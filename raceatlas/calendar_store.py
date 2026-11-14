"""Batch ICS ledger, caller-owned transaction under the already-held Account lock."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from raceatlas.models import PersonalCalendarEventStore
from raceatlas.planning import _actor_id
from raceatlas.planning_ics import EventMetadata, event_payloads, render_calendar
from raceatlas.planning_snapshot import PlanningLimitError, snapshot_documents


def materialize_calendar(session, actor, limits):
    account_id = _actor_id(session, actor)
    items = snapshot_documents(session, actor, limits=limits, calendar_only=True)
    payloads = event_payloads(items, account_id, limits)
    metadata = {}
    writes = []
    if payloads:
        stored = {
            row.scope_id: row
            for row in session.scalars(
                select(PersonalCalendarEventStore)
                .where(
                    PersonalCalendarEventStore.account_id == account_id,
                    PersonalCalendarEventStore.scope_id.in_([item.scope_id for item in payloads]),
                )
                .execution_options(populate_existing=True)
            )
        }
        count, stamp = session.execute(
            select(func.count(), func.clock_timestamp())
            .select_from(PersonalCalendarEventStore)
            .where(PersonalCalendarEventStore.account_id == account_id)
        ).one()
        if count + sum(item.scope_id not in stored for item in payloads) > limits.cache_pairs:
            raise PlanningLimitError()
        for payload in payloads:
            old = stored.get(payload.scope_id)
            fingerprint = payload.fingerprint
            changed = old is None or old.fingerprint != fingerprint
            sequence = 0 if old is None else old.sequence + int(changed)
            if sequence > 2147483647:
                raise PlanningLimitError()
            value = EventMetadata(stamp if changed else old.stamp, sequence)
            metadata[payload.scope_id] = value
            if changed:
                writes.append(
                    dict(
                        account_id=account_id,
                        scope_id=payload.scope_id,
                        fingerprint=fingerprint,
                        stamp=value.stamp,
                        sequence=sequence,
                    )
                )
    # Validate the COMPLETE bounded representation before any ledger mutation.
    result = render_calendar(payloads, metadata, limits)
    if writes:
        statement = insert(PersonalCalendarEventStore).values(writes)
        session.execute(
            statement.on_conflict_do_update(
                index_elements=[
                    PersonalCalendarEventStore.account_id,
                    PersonalCalendarEventStore.scope_id,
                ],
                set_={
                    key: getattr(statement.excluded, key)
                    for key in ("fingerprint", "stamp", "sequence")
                },
            )
        )
    return result
