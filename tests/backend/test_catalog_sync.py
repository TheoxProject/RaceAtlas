"""Offline provider fixture -> adapter -> sync -> public selection integration."""

from datetime import timedelta

from sqlalchemy import select, text
from test_catalog import SCENARIOS, request_page, validate
from test_sync import NOW, batch, observation

from raceatlas.models import CatalogState, ImportRun, ImportWindow, Race
from raceatlas.sync import LocationFact, synchronize
from raceatlas.sync.geocoding import CenterCandidate, OfflineProvider


def test_offline_fixture_import_flows_to_both_endpoints_and_invalidates_cursor(
    session, database, app
):
    assert (
        synchronize(database, [batch(observation(), observation("SECOND"))], checked_at=NOW).status
        == "success"
    )
    client = app.test_client()
    page = request_page(client, limit=1).json
    mapped = request_page(client, map_view=True, limit=1).json
    validate(page, "RacePage")
    validate(mapped, "MapPage")
    assert page["total"] == 2 and page["unlocated_count"] == 2
    assert mapped["features"] == [] and len(mapped["unlocated_ids"]) == 1
    assert page["items"][0]["race"]["source"]["source_season"] == 2027
    assert page["coverage"]["status"] == "consistent_sample"
    assert "synthétique" in page["coverage"]["note"]
    assert page["coverage"]["intrinsic_exhaustiveness"] == "unknown"
    # Same facts, new audit: freshness changes even though the race revision does not.
    later = NOW + timedelta(hours=1)
    assert (
        synchronize(
            database,
            [
                batch(
                    observation(checked=later), observation("SECOND", checked=later), checked=later
                )
            ],
            checked_at=later,
        ).status
        == "success"
    )
    assert request_page(client, cursor=page["next_cursor"]).status_code == 409
    assert request_page(client, map_view=True, cursor=mapped["next_cursor"]).status_code == 409
    assert all(race.revision == 1 for race in session.scalars(select(Race)))


def test_injected_commune_center_projects_one_feature_per_imported_race(session, database, app):
    first, second = observation(), observation("SECOND")
    facts = tuple(
        LocationFact(item.key, "Commune fictive", "26", "fixture-location-proof", "26999")
        for item in (first, second)
    )
    provider = OfflineProvider(
        "offline-test",
        "v1",
        lambda _: (CenterCandidate("26999", "Commune fictive", "26", 4.9, 45.1),),
    )
    result = synchronize(
        database, [batch(first, second, locations=facts)], checked_at=NOW, provider=provider
    )
    assert result.status == "success"
    page = request_page(app.test_client()).json
    mapped = request_page(app.test_client(), map_view=True).json
    validate(page, "RacePage")
    validate(mapped, "MapPage")
    assert page["total"] == mapped["total"] == 2
    assert page["unlocated_count"] == 0 and mapped["unlocated_ids"] == []
    assert {item["race"]["id"] for item in page["items"]} == {
        feature["id"] for feature in mapped["features"]
    }
    assert len({feature["properties"]["commune_id"] for feature in mapped["features"]}) == 1
    assert all(feature["geometry"]["coordinates"] == [4.9, 45.1] for feature in mapped["features"])


def test_coverage_uses_execution_order_retains_success_after_failure_then_recovers(
    session, database, app
):
    client = app.test_client()
    synchronize(database, [batch(observation())], checked_at=NOW)
    first = request_page(client).json["coverage"]
    success_at = first["last_successful_sync_at"]
    # Source clocks are deliberately older: execution order, not source time or UUID,
    # selects the newest attempt. An incomplete detail batch is a real failed sync.
    earlier = NOW - timedelta(days=1)
    failed = synchronize(
        database, [batch(keys=(observation().key,), checked=earlier)], checked_at=earlier
    )
    assert failed.status != "success"
    page = request_page(client).json
    coverage = page["coverage"]
    validate(page, "RacePage")
    assert coverage["status"] == "incomplete"
    assert coverage["last_successful_sync_at"] == success_at
    assert any(window["status"] == "incomplete" for window in coverage["windows"])
    later = NOW + timedelta(hours=2)
    synchronize(database, [batch(observation(checked=later), checked=later)], checked_at=later)
    recovered = request_page(client).json["coverage"]
    assert recovered["status"] == "consistent_sample"
    assert recovered["last_successful_sync_at"] != success_at


def test_legacy_audit_order_is_conservatively_incomplete(session, database, app):
    synchronize(database, [batch(observation())], checked_at=NOW)
    floor = session.scalar(select(ImportRun.catalog_order))
    session.get(CatalogState, 1).audit_floor = floor
    session.commit()
    coverage = request_page(app.test_client()).json["coverage"]
    assert coverage["status"] == "incomplete"
    assert coverage["windows"] == []
    assert coverage["last_successful_sync_at"] is not None
    assert "historiques" in coverage["note"]
    # Restore only test metadata; this field is immutable outside migration/tests.
    session.get(CatalogState, 1).audit_floor = 0
    session.commit()


def test_incoherent_success_window_is_never_claimed_consistent(session, database, app):
    synchronize(database, [batch(observation())], checked_at=NOW)
    window = session.scalar(select(ImportWindow))
    window.effective_department = "38"
    session.commit()
    coverage = request_page(app.test_client()).json["coverage"]
    assert coverage["status"] == "incomplete"
    assert coverage["windows"][0]["status"] == "incomplete"


def test_trigger_invalidation_on_seed_insert_delete_and_truncate(session, app):
    from raceatlas.seed import seed_synthetic

    client = app.test_client()
    initial = request_page(client).json["catalog_version"]
    seed_synthetic(session)
    session.commit()
    seeded = request_page(client).json
    assert seeded["catalog_version"] != initial
    assert seeded["total"] == len(SCENARIOS[0]["expected_ids"])
    session.delete(session.get(Race, "race-unlocated"))
    session.commit()
    deleted = request_page(client).json
    assert deleted["catalog_version"] != seeded["catalog_version"]
    session.execute(text("TRUNCATE race CASCADE"))
    session.commit()
    empty = request_page(client).json
    assert empty["catalog_version"] != deleted["catalog_version"]
    assert empty["total"] == 0
