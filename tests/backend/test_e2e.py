import json
import re
import threading
from pathlib import Path

import pytest
from map_support import (
    camera,
    camera_diagnostic,
    install_camera_diagnostic,
    intercept_map,
    launch,
    set_civil_date,
)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
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
    set_civil_date(page, now)
    intercept_map(page, **kwargs)
    page.goto(server)
    expect(page.locator(".map-canvas")).to_have_attribute("data-ready", "true", timeout=20000)


def assert_camera_unchanged(actual, expected):
    assert actual.keys() == expected.keys()
    for key in expected:
        if key == "center":
            # Sub-millimetre coordinate roundoff is not a reset; all other fields stay exact.
            assert actual[key] == pytest.approx(expected[key], abs=1e-9, rel=0)
        else:
            assert actual[key] == expected[key], key


def wait_camera_pitch(page, pitch):
    try:
        page.wait_for_function(
            "pitch => JSON.parse(document.querySelector('.map-canvas').dataset.camera)"
            ".pitch === pitch",
            arg=pitch,
            timeout=10000,
        )
    except PlaywrightTimeoutError as error:
        diagnostic = camera_diagnostic(page)
        try:
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / "summit.png"), timeout=5000)
        except Exception as screenshot_error:
            diagnostic["screenshot_error"] = type(screenshot_error).__name__
        raise AssertionError(
            f"Pitch {pitch} not reached within 10000ms; bounded camera diagnostic: "
            + json.dumps(diagnostic, ensure_ascii=True)
        ) from error


@pytest.mark.e2e
def test_civil_date_preserves_native_animation_clock(monkeypatch):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris")
        add_script = page.add_init_script

        def capture_native_then_install(script):
            # One init script fixes ordering: native references precede the actual helper.
            add_script(
                script="""globalThis.nativeClock = {
                Date, performance, now: performance.now,
                setTimeout, clearTimeout, setInterval, clearInterval,
                requestAnimationFrame, cancelAnimationFrame
            };"""
                + script
            )

        monkeypatch.setattr(page, "add_init_script", capture_native_then_install)
        set_civil_date(page, "2026-12-31T23:30:00Z")
        page.goto("data:text/html,<title>synthetic clock regression</title>")
        result = page.evaluate("""async () => {
            const native = globalThis.nativeClock;
            const fixed = native.Date.parse('2026-12-31T23:30:00Z');
            const original = new native.Date(2024, 1, 29, 12, 34, 56, 78);
            class DerivedDate extends Date {}
            const dates = Date.now() === fixed && +new Date() === fixed
                && Date() === new native.Date(fixed).toString()
                && +new Date(0) === 0 && Number.isNaN(+new Date(undefined))
                && +new Date('2024-02-29T12:00:00Z')
                    === native.Date.parse('2024-02-29T12:00:00Z')
                && +new Date(2024, 1, 29, 12, 34, 56, 78) === +original
                && new Date() instanceof native.Date && new Date() instanceof Date
                && new DerivedDate() instanceof DerivedDate
                && +new DerivedDate() === fixed
                && Date.parse === native.Date.parse && Date.UTC === native.Date.UTC
                && Date.UTC(2024, 1, 29) === native.Date.UTC(2024, 1, 29);
            const identities = performance === native.performance
                && performance.now === native.now
                && ['setTimeout','clearTimeout','setInterval','clearInterval',
                    'requestAnimationFrame','cancelAnimationFrame']
                    .every(key => globalThis[key] === native[key]);
            const paris = new Intl.DateTimeFormat('en-CA', {
                timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit'
            }).format(new Date());
            const readings = [performance.now()];
            for (let i = 0; i < 12; i++) {
                await new Promise(resolve => setTimeout(resolve, 0));
                readings.push(performance.now());
                const end = performance.now() + 2;
                while (performance.now() < end) {}
                readings.push(performance.now());
            }
            const frame = await new Promise(resolve => requestAnimationFrame(resolve));
            return {dates, identities, paris, clockInstalled: !!globalThis.__pwClock,
                monotone: readings.every((value, i) => !i || value >= readings[i - 1]),
                progressed: readings.at(-1) > readings[0], frame: Number.isFinite(frame),
                stillFixed: Date.now() === fixed && +new Date() === fixed};
        }""")
        assert result == {
            "dates": True,
            "identities": True,
            "paris": "2027-01-01",
            "clockInstalled": False,
            "monotone": True,
            "progressed": True,
            "frame": True,
            "stillFixed": True,
        }
        browser.close()


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
        assert_camera_unchanged(camera(page), before)
        page.get_by_role("button", name="Mois", exact=True).click()
        expect(page.get_by_label("Mois", exact=True)).to_be_visible()
        page.get_by_label("Mois", exact=True).select_option("2")
        expect(page.locator(".result-count")).to_contain_text("0 course")
        assert_camera_unchanged(camera(page), before)
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
        wait_camera_pitch(page, 60)
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
        initial_camera = camera(page)
        page.get_by_role("button", name="Zoom in", exact=True).click()
        page.wait_for_function(
            "zoom => JSON.parse(document.querySelector('.map-canvas').dataset.camera)"
            ".zoom === zoom",
            arg=initial_camera["zoom"] + 1,
            timeout=10000,
        )
        before = camera(page)
        assert before["zoom"] == initial_camera["zoom"] + 1
        # This comparator must reject an actual reset to the recorded initial camera.
        with pytest.raises(AssertionError):
            assert_camera_unchanged(initial_camera, before)
        page.get_by_role("button", name="Semaine ISO", exact=True).click()
        expect(page.get_by_label("Année ISO")).to_have_value("2026")
        expect(page.get_by_label("Semaine ISO", exact=True)).to_have_value("53")
        wait_period_filter(page, filters, "2026-12-28", "2027-01-03")
        expect(page.locator(".result-count strong")).to_have_text("1")
        for label, key, return_mode in [
            ("Année ISO", "Tab", "Année"),
            ("Année ISO", "Enter", "Mois"),
            ("Semaine ISO", "Tab", "Mois"),
            ("Semaine ISO", "Enter", "Année"),
        ]:
            page.get_by_role("button", name="Explorer les communes").click()
            page.get_by_role("button", name=re.compile("race-mtb-multiday")).click()
            selection_requests = [
                url for url in filters if re.search(r"/api/v1/(races|map)\?", url)
            ]
            field = page.get_by_label(label, exact=True)
            field.focus()
            field.press(key)
            page.get_by_role("button", name="Semaine ISO", exact=True).click()
            # Longer than the 180 ms debounce: no unchanged selection may trigger a request.
            page.wait_for_timeout(250)
            assert [
                url for url in filters if re.search(r"/api/v1/(races|map)\?", url)
            ] == selection_requests
            expect(
                page.get_by_role("heading", name="Course fictive race-mtb-multiday")
            ).to_be_visible()
            assert_camera_unchanged(camera(page), before)
            page.get_by_role("button", name="Fermer les détails").click()
            page.get_by_role("button", name=return_mode, exact=True).click()
            end = "2027-01-31" if return_mode == "Mois" else "2027-12-31"
            wait_period_filter(page, filters, "2027-01-01", end)
            expect(page.get_by_label("Année civile")).to_have_value("2027")
            if return_mode == "Mois":
                expect(page.get_by_label("Mois", exact=True)).to_have_value("1")
            assert_camera_unchanged(camera(page), before)
            page.get_by_role("button", name="Semaine ISO", exact=True).click()
            wait_period_filter(page, filters, "2026-12-28", "2027-01-03")
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
        assert_camera_unchanged(camera(page), before)
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
        assert install_camera_diagnostic(page)
        expect(
            page.get_by_text("Le fond de carte est partiellement indisponible.", exact=False)
        ).to_be_visible()
        expect(page.locator(".result-count")).to_contain_text("12 courses")
        expect(page.locator(".race-marker")).to_have_text("11", timeout=15000)
        page.get_by_role("button", name=re.compile("Summit")).click()
        page.wait_for_function(
            "Number(document.querySelector('.map-canvas').dataset.elevation) > 100"
        )
        expect(page.get_by_role("button", name=re.compile("Summit"))).to_have_attribute(
            "aria-pressed", "true"
        )
        wait_camera_pitch(page, 60)
        assert camera(page)["pitch"] == 60
        assert "snapshot" in camera_diagnostic(page)
        browser.close()


@pytest.mark.e2e
def test_pending_basemap_does_not_block_real_race_markers(seeded, server):
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page()
        pending = intercept_map(page, base_pending=True)
        set_civil_date(page, "2026-11-11T12:00:00Z")
        try:
            page.goto(server)
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            expect(page.locator(".result-count")).to_contain_text("12 courses")
            expect(page.locator(".race-marker")).to_have_text("11", timeout=15000)
            assert pending, "Basemap requests must still be held while race markers render"
        finally:
            try:
                for route in pending:
                    route.abort()
            finally:
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
        set_civil_date(page, "2026-11-11T12:00:00Z")
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
