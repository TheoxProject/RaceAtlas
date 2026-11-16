import json

import pytest
from sqlalchemy import event, select
from test_notifications import ONE, TWO, change, users

from raceatlas.models import Account, PersonalNotification
from raceatlas.notifications import project_notifications
from raceatlas.notifications_api import mark_all_notifications_read, read_notifications
from raceatlas.planning import put_saved_entry

KEY = b"synthetic-notification-cursor-key-000000"


def read(session, actor, **kwargs):
    return json.loads(read_notifications(session, actor, cursor_key=KEY, **kwargs))


@pytest.mark.parametrize("status", ["interested", "planned", "registered", "completed"])
def test_virtual_count_page_scope_graph_ack_all_and_replay(seeded, status):
    alice, bob = users(seeded)
    put_saved_entry(seeded, alice, ONE, status)
    put_saved_entry(seeded, alice, TWO, status)
    put_saved_entry(seeded, bob, TWO, status)
    change_id = change(seeded)
    seeded.commit()
    alice = seeded.get(Account, alice.id)
    queries = []

    def observe(_conn, _cursor, statement, *_args):
        queries.append(statement)

    event.listen(seeded.bind, "before_cursor_execute", observe)
    try:
        page = read(seeded, alice, limit=1)
    finally:
        event.remove(seeded.bind, "before_cursor_execute", observe)
    assert len([q for q in queries if "eligible_notifications" in q]) == 1
    assert page["unread_count"] == 2 and page["has_more"] and page["next_cursor"]
    item = page["items"][0]
    assert item["change_id"] == change_id and item["read_at"] is None
    assert item["entry"]["scope_id"] == item["entry"]["scope"]["id"] == item["scope_id"]
    assert item["entry"]["status"] == status
    assert item["entry"]["race"]["personal_eligibility"] == "not_evaluated"
    next_page = read(seeded, alice, limit=1, cursor=page["next_cursor"])
    assert next_page["unread_count"] == 2 and not next_page["has_more"]
    assert {item["scope_id"], next_page["items"][0]["scope_id"]} == {ONE, TWO}
    assert project_notifications(seeded, alice, batch_size=1).inserted == 1
    mark_all_notifications_read(seeded, alice)
    seeded.commit()
    after = read(seeded, alice)
    assert after["unread_count"] == 0 and all(i["read_at"] for i in after["items"])
    stamps = list(
        seeded.execute(select(PersonalNotification.scope_id, PersonalNotification.read_at))
    )
    mark_all_notifications_read(seeded, alice)
    seeded.commit()
    assert (
        list(seeded.execute(select(PersonalNotification.scope_id, PersonalNotification.read_at)))
        == stamps
    )
    assert read(seeded, bob)["unread_count"] == 1
