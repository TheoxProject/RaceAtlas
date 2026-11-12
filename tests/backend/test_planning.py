from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from threading import Barrier
from uuid import UUID

import pytest
import test_catalog as catalog_tests
import test_sync as source_tests
from sqlalchemy import event, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from raceatlas.models import (
    Account,
    CatalogState,
    EntryScope,
    ImportItem,
    Race,
    SavedEntry,
    SourceRevision,
)
from raceatlas.planning import (
    PlanningError,
    PlanningNotFound,
    create_account,
    delete_account,
    delete_saved_entry,
    get_saved_entry,
    list_saved_entries,
    normalize_email,
    put_saved_entry,
    update_saved_entry,
)
from raceatlas.sync import synchronize


def accounts(session):
    return create_account(session, "Alice@example.test"), create_account(
        session, "bob@example.test"
    )


def scopes(session):
    race = session.scalar(select(Race).where(Race.id == "race-road-split"))
    return race.scopes


def snapshot(entry):
    return (
        entry.id,
        entry.scope_id,
        entry.status,
        entry.created_at,
        entry.updated_at,
        entry.revision,
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        (" Alice.Example+tag@EXAMPLE.test \t", "alice.example+tag@example.test"),
        ("a+b@example.test", "a+b@example.test"),
        ("a.b@example.test", "a.b@example.test"),
    ],
)
def test_email_account_policy_keeps_dots_and_tags(value, expected):
    assert normalize_email(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        5,
        "",
        "a",
        "@example.test",
        "a@",
        "a@@b",
        "a b@c",
        "a@b\ncc",
        "a\x00@b",
        "a" * 250 + "@b.test",
    ],
)
def test_email_invalid_shape_never_echoes_input(value):
    with pytest.raises(PlanningError) as error:
        normalize_email(value)
    assert error.value.code == "invalid_email"
    assert str(error.value) == "Invalid email address."


def test_accounts_are_private_opaque_unique_and_not_credentials(session):
    first = create_account(session, " Alice.Example+tag@EXAMPLE.test ")
    session.flush()
    assert UUID(first.id).version == 4
    assert first.email_normalized == "alice.example+tag@example.test"
    assert first.created_at.utcoffset() == timedelta(0)
    assert not hasattr(first, "password_hash")
    with pytest.raises(PlanningError, match="^Account unavailable\\.$") as error:
        create_account(session, "ALICE.EXAMPLE+TAG@example.test")
    assert error.value.code == "account_unavailable"
    # A failed duplicate creation leaves the caller's transaction usable.
    distinct = [
        create_account(session, value)
        for value in ["aliceexample+tag@example.test", "alice.example@example.test"]
    ]
    assert len({first.id, *(account.id for account in distinct)}) == 3
    assert session.scalar(select(func.count()).select_from(Account)) == 3


@pytest.mark.parametrize("zone", ["UTC", "Europe/Paris", "Pacific/Honolulu"])
def test_private_timestamps_are_returned_as_utc_independently_of_database_session_zone(
    seeded, zone
):
    seeded.execute(select(func.set_config("TimeZone", zone, True)))
    alice = create_account(seeded, "timezone@example.test")
    entry = put_saved_entry(seeded, alice, scopes(seeded)[0].id)
    account_id, entry_id = alice.id, entry.id
    seeded.expire_all()
    account = seeded.get(Account, account_id)
    entry = get_saved_entry(seeded, account, entry_id)
    assert account.created_at.utcoffset() == timedelta(0)
    assert entry.created_at.utcoffset() == entry.updated_at.utcoffset() == timedelta(0)
    raw = seeded.scalar(text("SELECT created_at FROM saved_entry WHERE id=:id"), {"id": entry_id})
    assert raw == entry.created_at


def test_two_users_and_two_scopes_have_independent_statuses(seeded):
    session = seeded
    alice, bob = accounts(session)
    one, two = scopes(session)
    a = put_saved_entry(session, alice, one.id)
    b = put_saved_entry(session, bob, one.id, "registered")
    c = put_saved_entry(session, alice, two.id, "planned")
    assert len({a.id, b.id, c.id}) == 3
    assert "race_id" not in SavedEntry.__table__.columns
    assert a.scope.race_id == c.scope.race_id == "race-road-split"
    assert [(entry.scope_id, entry.status) for entry in list_saved_entries(session, bob)] == [
        (one.id, "registered")
    ]
    assert {entry.scope_id for entry in list_saved_entries(session, alice)} == {one.id, two.id}
    for entry in [a, b, c]:
        assert entry.created_at.utcoffset() == entry.updated_at.utcoffset() == timedelta(0)
        assert entry.revision == 1


def test_repeated_put_update_preserve_id_times_revision_and_target(seeded):
    alice, _ = accounts(seeded)
    scope = scopes(seeded)[0]
    loaded = put_saved_entry(seeded, alice, scope.id, "interested")
    first = snapshot(loaded)
    assert snapshot(put_saved_entry(seeded, alice, scope.id, "interested")) == first
    assert snapshot(update_saved_entry(seeded, alice, first[0], "interested")) == first
    for revision, status in enumerate(["planned", "registered", "completed"], start=2):
        entry = update_saved_entry(seeded, alice, first[0], status)
        assert entry.id == first[0] and entry.scope_id == scope.id
        assert entry.created_at == first[3] and entry.updated_at > first[4]
        assert entry.status == status and entry.revision == revision
        unchanged = snapshot(entry)
        assert snapshot(put_saved_entry(seeded, alice, scope.id, status)) == unchanged
    changed = put_saved_entry(seeded, alice, scope.id, "interested")
    assert changed.id == first[0] and changed.revision == 5
    assert changed is loaded and loaded.status == "interested" and loaded.revision == 5


@pytest.mark.parametrize("operation", ["read", "update", "invalid_update", "delete"])
def test_foreign_entry_and_missing_entry_are_indistinguishable(seeded, operation):
    alice, bob = accounts(seeded)
    entry = put_saved_entry(seeded, alice, scopes(seeded)[0].id, "planned")
    original = snapshot(entry)
    errors = []
    for entry_id in [entry.id, "unknown-entry"]:
        with pytest.raises(PlanningNotFound) as error:
            if operation == "read":
                get_saved_entry(seeded, bob, entry_id)
            elif operation.endswith("update"):
                update_saved_entry(
                    seeded, bob, entry_id, "bogus" if operation == "invalid_update" else "completed"
                )
            else:
                delete_saved_entry(seeded, bob, entry_id)
        errors.append((type(error.value), error.value.code, str(error.value)))
    assert errors[0] == errors[1]
    assert snapshot(get_saved_entry(seeded, alice, entry.id)) == original


@pytest.mark.parametrize("value", ["confirmed", "Registered", "", None, {}, 1])
def test_only_four_declarative_statuses_are_accepted(seeded, value):
    alice, _ = accounts(seeded)
    entry = put_saved_entry(seeded, alice, scopes(seeded)[0].id)
    first = snapshot(entry)
    for operation in [
        lambda: put_saved_entry(seeded, alice, entry.scope_id, value),
        lambda: update_saved_entry(seeded, alice, entry.id, value),
    ]:
        with pytest.raises(PlanningError) as error:
            operation()
        assert error.value.code == "invalid_status"
    assert snapshot(get_saved_entry(seeded, alice, entry.id)) == first


def test_actor_must_be_a_server_loaded_account_in_the_current_session(seeded, database):
    alice, _ = accounts(seeded)
    seeded.commit()
    for actor in [
        alice.id,
        {"id": alice.id},
        Account(id=alice.id, email_normalized=alice.email_normalized),
        None,
    ]:
        with pytest.raises(PlanningNotFound):
            list_saved_entries(seeded, actor)
    with Session(database) as other:
        with pytest.raises(PlanningNotFound):
            list_saved_entries(other, alice)


def test_missing_scope_and_invalid_targets_leave_transaction_usable(seeded):
    alice, _ = accounts(seeded)
    for value in ["unknown-scope", None, {}, "x" * 65]:
        with pytest.raises(PlanningNotFound):
            put_saved_entry(seeded, alice, value)
    entry = put_saved_entry(seeded, alice, scopes(seeded)[0].id)
    assert get_saved_entry(seeded, alice, entry.id).id == entry.id


@pytest.mark.parametrize("expired", [False, True], ids=["loaded", "expired"])
@pytest.mark.parametrize("operation", ["list", "get", "put", "update", "delete", "delete_account"])
def test_pending_deleted_actor_is_rejected_before_refresh_or_autoflush(seeded, expired, operation):
    alice, bob = accounts(seeded)
    scope_id = scopes(seeded)[0].id
    own = put_saved_entry(seeded, alice, scope_id)
    other = put_saved_entry(seeded, bob, scope_id, "registered")
    account_id, entry_id, other_before = alice.id, own.id, snapshot(other)
    seeded.commit()
    if not expired:
        assert alice.id == account_id
    seeded.delete(alice)
    assert inspect(alice).persistent and alice in seeded.deleted
    queries = []

    def capture(*args):
        queries.append(1)

    event.listen(seeded.bind, "before_cursor_execute", capture)
    try:
        with pytest.raises(PlanningNotFound, match="^Saved entry not found\\.$"):
            if operation == "list":
                list_saved_entries(seeded, alice)
            elif operation == "get":
                get_saved_entry(seeded, alice, entry_id)
            elif operation == "put":
                put_saved_entry(seeded, alice, scope_id)
            elif operation == "update":
                update_saved_entry(seeded, alice, entry_id, "completed")
            elif operation == "delete":
                delete_saved_entry(seeded, alice, entry_id)
            else:
                delete_account(seeded, alice)
    finally:
        event.remove(seeded.bind, "before_cursor_execute", capture)
    assert queries == []
    assert alice in seeded.deleted and seeded.is_active
    with seeded.no_autoflush:
        assert seeded.scalar(select(1)) == 1
        assert seeded.scalar(select(Account.id).where(Account.id == account_id)) == account_id
    # The caller, not a rejected service operation, decides when to flush its deletion.
    seeded.flush()
    assert snapshot(put_saved_entry(seeded, bob, scope_id, "registered")) == other_before


@pytest.mark.parametrize(
    "target",
    ["bad\x00scope", "bad\ud800scope", "bad\udfffscope"],
    ids=["nul", "high-surrogate", "low-surrogate"],
)
@pytest.mark.parametrize("operation", ["get", "put", "update", "delete"])
def test_nonrepresentable_targets_are_generic_and_leave_transaction_usable(
    seeded, target, operation
):
    alice, _ = accounts(seeded)
    scope_id = scopes(seeded)[0].id
    before = snapshot(put_saved_entry(seeded, alice, scope_id))
    queries = []

    def capture(*args):
        queries.append(1)

    event.listen(seeded.bind, "before_cursor_execute", capture)
    try:
        with pytest.raises(PlanningNotFound, match="^Saved entry not found\\.$"):
            if operation == "get":
                get_saved_entry(seeded, alice, target)
            elif operation == "put":
                put_saved_entry(seeded, alice, target)
            elif operation == "update":
                update_saved_entry(seeded, alice, target, "planned")
            else:
                delete_saved_entry(seeded, alice, target)
    finally:
        event.remove(seeded.bind, "before_cursor_execute", capture)
    assert queries == [] and seeded.is_active
    assert seeded.scalar(select(1)) == 1
    assert snapshot(put_saved_entry(seeded, alice, scope_id)) == before


def test_valid_unicode_and_synthetic_targets_are_not_restricted_to_uuids(seeded):
    alice, _ = accounts(seeded)
    scope = EntryScope(
        id="scope-synthétique-🚲",
        race_id="race-road-split",
        position=99,
        kind="entry_list",
        identity_status="unverified",
        eligibility_status="unknown",
        raw_label="Synthetic UTF-8 target",
    )
    seeded.add(scope)
    seeded.flush()
    entry = SavedEntry(
        id="saved-synthétique-🚲", account_id=alice.id, scope_id=scope.id, status="interested"
    )
    seeded.add(entry)
    seeded.flush()
    entry_id = entry.id
    assert get_saved_entry(seeded, alice, entry_id) is entry
    assert put_saved_entry(seeded, alice, scope.id) is entry
    assert update_saved_entry(seeded, alice, entry_id, "planned").revision == 2
    delete_saved_entry(seeded, alice, entry_id)
    with pytest.raises(PlanningNotFound):
        get_saved_entry(seeded, alice, entry_id)


def test_account_deletion_cascades_only_its_private_rows(seeded):
    alice, bob = accounts(seeded)
    scope_ids = [scope.id for scope in scopes(seeded)]
    own = put_saved_entry(seeded, alice, scope_ids[0])
    own_id = own.id
    other = put_saved_entry(seeded, bob, scope_ids[0], "completed")
    other_snapshot = snapshot(other)
    delete_account(seeded, alice)
    assert seeded.scalar(select(SavedEntry).where(SavedEntry.id == own_id)) is None
    assert snapshot(get_saved_entry(seeded, bob, other.id)) == other_snapshot
    assert (
        seeded.scalar(
            select(func.count()).select_from(EntryScope).where(EntryScope.id.in_(scope_ids))
        )
        == 2
    )
    assert seeded.get(Race, "race-road-split") is not None


def test_private_writes_do_not_invalidate_public_catalogue_or_leak_identity(seeded, app):
    client = app.test_client()
    before = catalog_tests.request_page(client).json["catalog_version"]
    before_revision = seeded.scalar(select(CatalogState.revision))
    alice, bob = accounts(seeded)
    entry = put_saved_entry(seeded, alice, scopes(seeded)[0].id)
    seeded.commit()
    for status in ["planned", "registered", "completed"]:
        update_saved_entry(seeded, alice, entry.id, status)
        seeded.commit()
    response = catalog_tests.request_page(client)
    assert response.json["catalog_version"] == before
    assert alice.id not in response.text and alice.email_normalized not in response.text
    delete_saved_entry(seeded, alice, entry.id)
    delete_account(seeded, alice)
    delete_account(seeded, bob)
    seeded.commit()
    assert catalog_tests.request_page(client).json["catalog_version"] == before
    assert seeded.scalar(select(CatalogState.revision)) == before_revision


def test_database_restricts_scope_deletion_and_invalid_private_rows(seeded):
    alice, _ = accounts(seeded)
    bare_scope = EntryScope(
        race_id="race-road-split",
        position=99,
        kind="entry_list",
        identity_status="unverified",
        eligibility_status="unknown",
        raw_label="Synthetic scope referenced only by saved entries",
    )
    seeded.add(bare_scope)
    seeded.flush()
    entry = put_saved_entry(seeded, alice, bare_scope.id)
    params = {"account": alice.id, "scope": entry.scope_id}
    statements = [
        ("DELETE FROM entry_scope WHERE id=:scope", "23503"),
        (
            "INSERT INTO account(id,email_normalized) VALUES ('duplicate','alice@example.test')",
            "23505",
        ),
        (
            "INSERT INTO account(id,email_normalized) VALUES ('uppercase','OTHER@example.test')",
            "23514",
        ),
        (
            "INSERT INTO saved_entry(id,account_id,scope_id,status) "
            "VALUES ('duplicate',:account,:scope,'interested')",
            "23505",
        ),
        ("UPDATE saved_entry SET status='confirmed' WHERE scope_id=:scope", "23514"),
        ("UPDATE saved_entry SET revision=0 WHERE scope_id=:scope", "23514"),
        (
            "UPDATE saved_entry SET updated_at=created_at-interval '1 second' "
            "WHERE scope_id=:scope",
            "23514",
        ),
    ]
    for statement, state in statements:
        with pytest.raises(IntegrityError) as error:
            with seeded.begin_nested():
                seeded.execute(text(statement), params)
        assert error.value.orig.sqlstate == state
        if statement.startswith("DELETE FROM entry_scope"):
            assert error.value.orig.diag.constraint_name == "fk_saved_entry_scope_id_entry_scope"
    assert get_saved_entry(seeded, alice, entry.id).status == "interested"


@pytest.mark.parametrize("different_statuses", [False, True])
def test_concurrent_postgresql_puts_keep_one_identity_and_count_real_changes(
    seeded, database, different_statuses
):
    alice, _ = accounts(seeded)
    account_id, scope_id = alice.id, scopes(seeded)[0].id
    initial = snapshot(put_saved_entry(seeded, alice, scope_id)) if different_statuses else None
    seeded.commit()
    barrier = Barrier(2)

    def writer(status):
        with Session(database) as session:
            session.execute(text("SET LOCAL statement_timeout = '5s'"))
            actor = session.get(Account, account_id)
            barrier.wait(timeout=10)
            entry = put_saved_entry(session, actor, scope_id, status)
            result = snapshot(entry)
            session.commit()
            return result

    statuses = ["planned", "registered"] if different_statuses else ["planned", "planned"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(writer, status) for status in statuses]
        results = [future.result(timeout=15) for future in futures]
    seeded.expire_all()
    entry = list_saved_entries(seeded, seeded.get(Account, account_id))[0]
    assert results[0][0] == results[1][0] == entry.id
    assert seeded.scalar(select(func.count()).select_from(SavedEntry)) == 1
    if different_statuses:
        assert entry.id == initial[0] and entry.revision == 3
        assert {result[5] for result in results} == {2, 3}
        assert entry.status in statuses
    else:
        assert results[0] == results[1] == snapshot(entry)
        assert entry.revision == 1


def saved_import(session, database):
    first = source_tests.observation()
    assert (
        synchronize(database, [source_tests.batch(first)], checked_at=source_tests.NOW).status
        == "success"
    )
    race = session.scalar(select(Race))
    proof = source_tests.identities(first, race)
    alice, bob = accounts(session)
    entries = [
        put_saved_entry(session, alice, race.scopes[0].id, "planned"),
        put_saved_entry(session, bob, race.scopes[0].id, "registered"),
        put_saved_entry(session, alice, race.scopes[1].id, "completed"),
    ]
    expected = {entry.id: snapshot(entry) for entry in entries}
    session.commit()
    return first, race.id, proof, expected


def assert_import_favorites(session, expected, race_id):
    session.expire_all()
    entries = session.scalars(select(SavedEntry)).all()
    assert {entry.id: snapshot(entry) for entry in entries} == expected
    assert {entry.scope.race_id for entry in entries} == {race_id}


def test_source_rename_postpone_attested_reorder_and_replay_preserve_saved_targets(
    session, database
):
    first, race_id, proof, expected = saved_import(session, database)
    later = source_tests.NOW + timedelta(hours=1)
    renamed = replace(
        first,
        name="Synthetic renamed event",
        start_date=first.start_date + timedelta(days=1),
        end_date=first.end_date + timedelta(days=1),
        status="postponed",
        checked_at=later,
    )
    assert (
        synchronize(database, [source_tests.batch(renamed, checked=later)], checked_at=later).status
        == "success"
    )
    assert_import_favorites(session, expected, race_id)
    before_ids = [scope.id for scope in session.get(Race, race_id).scopes]
    later += timedelta(hours=1)
    reordered = replace(renamed, scopes=tuple(reversed(renamed.scopes)), checked_at=later)
    result = synchronize(
        database,
        [source_tests.batch(reordered, checked=later, identities=(proof,))],
        checked_at=later,
    )
    assert result.status == "success"
    assert_import_favorites(session, expected, race_id)
    stored = session.get(Race, race_id)
    assert [scope.id for scope in stored.scopes] == list(reversed(before_ids))
    revision = stored.revision
    assert stored.name == renamed.name and stored.start_date == renamed.start_date
    replay = synchronize(database, [source_tests.batch(reordered, checked=later)], checked_at=later)
    assert replay.status == "success"
    assert_import_favorites(session, expected, race_id)
    assert session.get(Race, race_id).revision == revision
    item = session.scalar(
        select(ImportItem).where(
            ImportItem.window_id.in_(
                select(source_tests.ImportWindow.id).where(
                    source_tests.ImportWindow.run_id == result.run_id
                )
            )
        )
    )
    assert item.observed["identity_evidence"] == proof.evidence_id


@pytest.mark.parametrize("change", ["ambiguous", "remove", "split", "move_rule"])
def test_source_identity_refusals_keep_all_private_entries_and_public_graph(
    session, database, change
):
    first, race_id, proof, expected = saved_import(session, database)
    original = session.get(Race, race_id)
    graph = [(scope.id, [rule.id for rule in scope.rules]) for scope in original.scopes]
    if change == "ambiguous":
        changed = replace(first, scopes=tuple(reversed(first.scopes)))
        attestations = ()
    elif change == "remove":
        changed = replace(first, scopes=first.scopes[:1])
        attestations = (proof,)
    elif change == "split":
        a, b = first.scopes
        split = replace(a, token="synthetic-new-split", rules=a.rules[1:])
        changed = replace(first, scopes=(replace(a, rules=a.rules[:1]), b, split))
        attestations = (proof,)
    else:
        a, b = first.scopes
        changed = replace(
            first, scopes=(replace(a, rules=a.rules[:1]), replace(b, rules=(*b.rules, a.rules[1])))
        )
        attestations = (proof,)
    later = source_tests.NOW + timedelta(hours=1)
    changed = replace(changed, checked_at=later)
    result = synchronize(
        database,
        [source_tests.batch(changed, checked=later, identities=attestations)],
        checked_at=later,
    )
    assert result.status == "failed"
    assert_import_favorites(session, expected, race_id)
    assert [
        (scope.id, [rule.id for rule in scope.rules]) for scope in session.get(Race, race_id).scopes
    ] == graph
    assert session.scalar(select(func.count()).select_from(SourceRevision)) == 1
    audit = session.scalars(select(ImportItem).where(ImportItem.status == "review")).one()
    assert audit.diagnostic == (
        "scope_identity_needs_review" if change == "ambiguous" else "identity_needs_review"
    )


def test_controlled_source_absence_keeps_saved_scope_and_declared_status(session, database):
    _, race_id, _, expected = saved_import(session, database)
    later = source_tests.NOW + timedelta(hours=1)
    result = synchronize(database, [source_tests.batch(checked=later)], checked_at=later)
    assert result.status == "success" and result.missing_marked == 1
    assert_import_favorites(session, expected, race_id)
    assert session.get(Race, race_id).source_presence == "to_verify"
