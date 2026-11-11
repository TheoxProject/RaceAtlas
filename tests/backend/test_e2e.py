import re
import threading
from pathlib import Path

import pytest
from map_support import camera, intercept_map, launch
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import text
from werkzeug.serving import make_server

from raceatlas import create_app
from raceatlas.models import Commune, Race

SHOTS = Path(__file__).resolve().parents[2] / ".local-tools" / "lot5-screenshots"


@pytest.fixture()
def server(app):
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)


def open_map(page, server, *, now="2026-11-11T12:00:00Z", **kwargs):
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.clock.set_fixed_time(now)
    intercept_map(page, **kwargs)
    page.goto(server)
    expect(page.locator(".map-canvas")).to_have_attribute("data-ready", "true", timeout=20000)


@pytest.mark.e2e
def test_compiled_react_flask_postgresql(seeded, server):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(viewport={"width": 1440, "height": 960}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        open_map(page, server)
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        expect(page.locator(".race-marker").first).to_be_visible(timeout=20000)
        assert page.locator("canvas.maplibregl-canvas").evaluate(
            '(canvas) => !!canvas.getContext("webgl2")'
        )
        expect(page.get_by_role("button", name=re.compile("Altitude"))).to_have_attribute(
            "aria-pressed", "true"
        )
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / "desktop.png"))
        before = camera(page)
        previous_marker = page.locator(".race-marker").get_attribute("style")
        seeded.execute(text("UPDATE commune SET longitude = longitude + 0.1"))
        seeded.commit()
        page.get_by_role("button", name="Actualiser les courses").click()
        page.wait_for_function(
            "previous => { const marker = document.querySelector('.race-marker'); "
            "return marker && marker.getAttribute('style') !== previous; }",
            arg=previous_marker,
        )
        assert camera(page) == before
        page.get_by_role("button", name="Mois", exact=True).click()
        expect(page.get_by_label("Mois", exact=True)).to_be_visible()
        page.get_by_label("Mois", exact=True).select_option("2")
        expect(page.locator(".result-count")).to_contain_text("0 course")
        assert camera(page) == before
        page.get_by_role("button", name="Année", exact=True).click()
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        page.get_by_role("button", name="Explorer les communes").click()
        page.get_by_role("button", name=re.compile("Course fictive race-access-ambiguous")).click()
        expect(
            page.get_by_role("heading", name="Course fictive race-access-ambiguous")
        ).to_be_visible()
        expect(page.get_by_text("Catégories ambiguës", exact=False)).to_be_visible()
        seeded.execute(
            text(
                "UPDATE race SET name = 'Épreuve modifiée dans PostgreSQL' "
                "WHERE id = 'race-access-ambiguous'"
            )
        )
        seeded.commit()
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name="Actualiser les courses").click()
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        page.get_by_role("button", name="Explorer les communes").click()
        expect(
            page.get_by_role("button", name=re.compile("Épreuve modifiée dans PostgreSQL"))
        ).to_be_visible()
        page.get_by_role("button", name=re.compile("Épreuve modifiée dans PostgreSQL")).click()
        expect(page.get_by_role("heading", name="Épreuve modifiée dans PostgreSQL")).to_be_visible()
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name=re.compile("Summit")).click()
        expect(page.locator(".map-canvas")).to_have_attribute("data-terrain", "summit")
        expect(page.locator(".map-canvas")).to_have_attribute(
            "data-elevation", re.compile(r"[0-9]"), timeout=15000
        )
        page.wait_for_function(
            "Number(document.querySelector('.map-canvas').dataset.elevation) > 100"
        )
        page.wait_for_timeout(700)
        assert camera(page)["pitch"] == 60
        page.screenshot(path=str(SHOTS / "summit.png"))
        assert not errors
        browser.close()


@pytest.mark.e2e
def test_compiled_mobile_filters_nonlocalized_and_radius(seeded, server):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(
            viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=1
        )
        open_map(page, server)
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        expect(page.locator(".race-marker")).to_have_text("11", timeout=15000)
        expect(page.locator(".race-marker")).to_be_visible()
        assert_attribution_unobscured(page)
        page.screenshot(path=str(SHOTS / "mobile.png"))
        page.get_by_role("button", name="Explorer les communes").click()
        assert_attribution_unobscured(page)
        page.get_by_role("button", name=re.compile("Course fictive race-access-ambiguous")).click()
        assert_attribution_unobscured(page)
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name=re.compile("Filtres")).click()
        page.get_by_label("Route", exact=True).check()
        page.get_by_label("open 1", exact=True).check()
        page.get_by_label("open 2", exact=True).check()
        page.get_by_role("button", name="Toutes ensemble").click()
        page.get_by_role("button", name="Voir les courses sur la carte").click()
        expect(page.locator(".result-count")).to_contain_text("2 courses")
        page.get_by_role("button", name=re.compile("Filtres")).click()
        page.get_by_role("button", name="Réinitialiser les filtres").click()
        page.get_by_label("Zone", exact=True).select_option("radius")
        page.get_by_label("Longitude", exact=True).fill("0")
        page.get_by_label("Latitude", exact=True).fill("0")
        page.get_by_role("button", name="Choisir ce point").click()
        page.get_by_role("button", name="Voir les courses sur la carte").click()
        expect(page.locator(".result-count")).to_contain_text("0 course")
        page.get_by_role("button", name="1 localisation à préciser ↗").click()
        page.get_by_role("button", name=re.compile("Course fictive race-unlocated")).click()
        expect(page.get_by_text("cette course n’est pas comptée", exact=False)).to_be_visible()
        expect(page.get_by_text("Centre de commune non disponible")).to_be_visible()
        assert_attribution_unobscured(page)
        page.screenshot(path=str(SHOTS / "mobile-details.png"))
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        browser.close()


def assert_attribution_unobscured(page):
    expect(page.locator(".map-attribution a")).to_have_count(4)
    assert page.locator(".map-attribution a").evaluate_all("""links => links.every(link => {
        const rect = link.getBoundingClientRect();
        const hit = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
        return hit && link.contains(hit);
    })""")


@pytest.mark.e2e
def test_new_year_iso_inputs_and_clean_screenshot_directory(seeded, server, monkeypatch, tmp_path):
    screenshots = tmp_path / "absent-parent" / "screenshots"
    monkeypatch.setattr(__import__(__name__), "SHOTS", screenshots)
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        filters = []
        page.on("request", lambda request: filters.append(request.url))
        open_map(page, server, now="2027-01-01T12:00:00Z")
        assert screenshots.is_dir()
        expect(page.get_by_label("Année civile")).to_have_value("2027")
        expect(page.locator(".result-count strong")).to_have_text("1")
        expect(page.locator(".race-marker")).to_be_visible(timeout=15000)
        # Capture after the initial 500 ms camera transition, before changing any period.
        page.wait_for_timeout(700)
        before = camera(page)
        page.get_by_role("button", name="Semaine ISO", exact=True).click()
        expect(page.get_by_label("Année ISO")).to_have_value("2026")
        expect(page.get_by_label("Semaine ISO", exact=True)).to_have_value("53")
        wait_period_filter(page, filters, "2026-12-28", "2027-01-03")
        expect(page.locator(".result-count strong")).to_have_text("1")
        page.get_by_role("button", name="Explorer les communes").click()
        expect(page.get_by_role("button", name=re.compile("race-mtb-multiday"))).to_be_visible()
        page.get_by_role("button", name="Fermer les détails").click()
        for label, invalid, restored in [
            ("Année ISO", "2026.5", "2026"),
            ("Semaine ISO", "2.5", "53"),
            ("Semaine ISO", "", "53"),
            ("Semaine ISO", "0", "53"),
            ("Semaine ISO", "-1", "53"),
        ]:
            field = page.get_by_label(label, exact=True)
            field.fill(invalid)
            field.press("Tab")
            expect(field).to_have_value(restored)
        wait_period_filter(page, filters, "2026-12-28", "2027-01-03")
        page.get_by_label("Année ISO").fill("2027")
        page.get_by_label("Année ISO").press("Enter")
        expect(page.get_by_label("Semaine ISO", exact=True)).to_have_value("52")
        wait_period_filter(page, filters, "2027-12-27", "2028-01-02")
        page.get_by_label("Semaine ISO", exact=True).fill("54")
        page.get_by_label("Semaine ISO", exact=True).press("Enter")
        expect(page.get_by_label("Semaine ISO", exact=True)).to_have_value("52")
        page.get_by_role("button", name="Année", exact=True).click()
        page.get_by_label("Année civile").fill("2027.5")
        page.get_by_label("Année civile").press("Enter")
        expect(page.get_by_label("Année civile")).to_have_value("2027")
        wait_period_filter(page, filters, "2027-01-01", "2027-12-31")
        assert camera(page) == before
        browser.close()


def wait_period_filter(page, requests, start, end):
    import json
    from urllib.parse import parse_qs, urlparse

    def last_filter():
        urls = [url for url in requests if "/api/v1/races?" in url]
        return json.loads(parse_qs(urlparse(urls[-1]).query)["filter"][0]) if urls else {}

    expect(page.locator(".result-count")).not_to_contain_text("Recherche")
    for _ in range(100):
        if last_filter().get("from") == start and last_filter().get("to") == end:
            return
        page.wait_for_timeout(50)
    assert last_filter().get("from") == start and last_filter().get("to") == end


@pytest.mark.e2e
def test_dem_failure_keeps_altitude_and_races(seeded, server):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        open_map(page, server, dem_failure=True)
        expect(page.get_by_text("Le relief est indisponible.", exact=False)).to_be_visible(
            timeout=15000
        )
        expect(page.get_by_role("button", name=re.compile("Altitude"))).to_have_attribute(
            "aria-pressed", "true"
        )
        expect(page.get_by_role("button", name=re.compile("Summit"))).to_be_disabled()
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        expect(page.locator(".race-marker")).to_have_text("11", timeout=15000)
        page.screenshot(path=str(SHOTS / "dem-failure.png"))
        browser.close()


@pytest.mark.e2e
def test_base_map_warning_does_not_silently_disable_summit(seeded, server):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page()
        open_map(page, server, base_failure=True)
        expect(
            page.get_by_text("Le fond de carte est partiellement indisponible.", exact=False)
        ).to_be_visible()
        page.get_by_role("button", name=re.compile("Summit")).click()
        page.wait_for_function(
            "Number(document.querySelector('.map-canvas').dataset.elevation) > 100"
        )
        expect(page.get_by_role("button", name=re.compile("Summit"))).to_have_attribute(
            "aria-pressed", "true"
        )
        assert camera(page)["pitch"] == 60
        browser.close()


@pytest.mark.e2e
def test_commune_group_then_real_spatial_cluster_distinct_race_count(seeded, server):
    race = seeded.get(Race, "race-gravel")
    original = race.commune
    neighbor = Commune(
        id="commune-neighbor",
        insee_code="26998",
        name="Voisine synthétique",
        department="26",
        longitude=original.longitude + 0.05,
        latitude=original.latitude,
        precision="commune_center",
        provenance="synthetic",
    )
    seeded.add(neighbor)
    race.commune = neighbor
    race.source.source_season = 2027
    seeded.commit()
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        open_map(page, server)
        expect(page.locator(".result-count")).to_contain_text("2 communes")
        cluster = page.get_by_role("button", name="11 courses regroupées, agrandir")
        expect(cluster).to_be_visible(timeout=15000)
        cluster.click()
        neighbor_marker = page.get_by_role("button", name="1 course à Voisine synthétique")
        expect(neighbor_marker).to_be_visible(timeout=15000)
        neighbor_marker.focus()
        neighbor_marker.press("Enter")
        expect(page.get_by_role("heading", name="Course fictive race-gravel")).to_be_visible()
        expect(page.get_by_text("saison source 2027", exact=False)).to_be_visible()
        assert page.get_by_label("Année civile").input_value() == "2026"
        page.screenshot(path=str(SHOTS / "cluster-details.png"))
        browser.close()


@pytest.mark.e2e
def test_catalogue_409_is_bounded_and_retry_reloads_real_postgresql(seeded, server):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page()
        attempts = []

        def stale(route):
            attempts.append(route.request.url)
            route.fulfill(status=409, json={"code": "stale_cursor"})

        page.route("**/api/v1/races?**", stale)
        open_map(page, server)
        expect(page.get_by_role("heading", name="Le catalogue évolue.")).to_be_visible()
        assert len(attempts) == 3
        page.unroute("**/api/v1/races?**", stale)
        page.get_by_role("button", name="Réessayer", exact=True).click()
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        browser.close()


@pytest.mark.e2e
def test_webgl_unavailable_keeps_accessible_race_details(seeded, server):
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--disable-webgl"])
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        intercept_map(page)
        page.clock.set_fixed_time("2026-11-11T12:00:00Z")
        page.goto(server)
        expect(
            page.get_by_text("La carte est indisponible sur cet appareil.", exact=False)
        ).to_be_visible()
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        page.get_by_role("button", name="Explorer les communes").click()
        page.get_by_role("button", name=re.compile("Course fictive race-cancelled")).click()
        expect(page.get_by_text("Course annulée selon la source.")).to_be_visible()
        page.screenshot(path=str(SHOTS / "webgl-failure.png"))
        assert not errors
        browser.close()


@pytest.mark.e2e
def test_compiled_empty_database(session, server):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page()
        open_map(page, server)
        expect(
            page.get_by_role("heading", name="Aucune course dans cette sélection")
        ).to_be_visible()
        browser.close()


@pytest.mark.e2e
def test_compiled_database_unavailable(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://wrong:private@127.0.0.1:1/absent")
    app = create_app()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = launch(playwright)
            page = browser.new_page()
            intercept_map(page)
            page.goto(f"http://127.0.0.1:{server.server_port}")
            expect(
                page.get_by_role("heading", name="Service temporairement indisponible.")
            ).to_be_visible()
            assert "private" not in page.content()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        app.extensions["database"].dispose()
