import base64
import json

import pytest
from sqlalchemy import event
from test_notifications import ONE, TWO, change, users
from test_notifications_api import read

from raceatlas.notifications_api import NotificationQueryError, parse_query
from raceatlas.planning import create_account, put_saved_entry


@pytest.mark.parametrize(
    "limit,cursor",
    [
        (True, None),
        (101, None),
        ("١", None),
        (50, "x" * 1025),
        (50, base64.urlsafe_b64encode(b"null").decode().rstrip("=") + "." + "a" * 43),
        (
            50,
            base64.urlsafe_b64encode(
                json.dumps([1, "2026-99-99T00:00:00Z", "change", "scope"]).encode()
            )
            .decode()
            .rstrip("=")
            + "."
            + "a" * 43,
        ),
    ],
)
def test_pure_notification_query_bounds(limit, cursor):
    with pytest.raises(NotificationQueryError):
        parse_query(limit, cursor)


def test_cursor_wrong_actor_tampered_and_recreated_account_fail_before_private_sql(seeded):
    alice, bob = users(seeded)
    put_saved_entry(seeded, alice, ONE)
    put_saved_entry(seeded, alice, TWO)
    put_saved_entry(seeded, bob, ONE)
    change(seeded)
    seeded.commit()
    cursor = read(seeded, alice, limit=1)["next_cursor"]
    queries = []

    def observe(*_args):
        queries.append(True)

    event.listen(seeded.bind, "before_cursor_execute", observe)
    try:
        for actor, invalid in [
            (bob, cursor),
            (alice, cursor[:-1] + ("A" if cursor[-1] != "A" else "B")),
        ]:
            with pytest.raises(NotificationQueryError):
                read(seeded, actor, cursor=invalid)
        assert queries == []
    finally:
        event.remove(seeded.bind, "before_cursor_execute", observe)
    seeded.delete(alice)
    seeded.commit()
    recreated = create_account(seeded, "alice@example.test")
    seeded.commit()
    with pytest.raises(NotificationQueryError):
        read(seeded, recreated, cursor=cursor)
    assert read(seeded, bob)["unread_count"] == 1
