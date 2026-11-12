import re
from contextlib import contextmanager
from pathlib import Path

import pytest
import test_e2e as map_tests
from map_support import camera, launch
from playwright.sync_api import expect, sync_playwright
from test_e2e import (
    assert_attribution_unobscured,
    assert_camera_unchanged,
    open_map,
    wait_camera_pitch,
)

SHOTS = Path(__file__).resolve().parents[2] / ".local-tools" / "lot6-screenshots"
server = map_tests.server


@contextmanager
def calendar_page(server, shot, *, mobile=False, now="2026-11-11T12:00:00Z"):
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(
            viewport={"width": 390 if mobile else 1440, "height": 844 if mobile else 960},
            is_mobile=mobile,
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            open_map(page, server, now=now)
            yield page
            assert not errors
        except Exception:
            try:
                page.screenshot(path=str(SHOTS / shot), timeout=5000)
            except Exception:
                pass
            raise
        finally:
            browser.close()


def ready_calendar(page, total):
    expect(page.locator(".calendar-view")).to_have_attribute("aria-busy", "false")
    expect(page.locator(".calendar-summary")).to_have_text(
        f"{total} course{'s' if total != 1 else ''} ce mois-ci"
    )


def reach_last_day(page, date, month_title):
    last = page.locator(f'td[data-date="{date}"] .calendar-day')
    last.scroll_into_view_if_needed()
    expect(last).to_be_visible()
    last.click()
    expect(page.get_by_text("Aucune course ce jour.")).to_be_visible()
    page.get_by_role("button", name="Fermer les détails").click()
    page.get_by_role("heading", name=month_title).scroll_into_view_if_needed()


@pytest.mark.e2e
def test_calendar_new_year_multiday_and_live_map_camera(seeded, server):
    with calendar_page(server, "desktop.png", now="2027-01-01T12:00:00Z") as page:
        expect(page.locator(".result-count strong")).to_have_text("1")
        page.get_by_role("button", name="Zoom in", exact=True).click()
        page.wait_for_function(
            "JSON.parse(document.querySelector('.map-canvas').dataset.camera).zoom === 7.5"
        )
        page.get_by_role("button", name=re.compile("Summit")).click()
        page.wait_for_function(
            "Number(document.querySelector('.map-canvas').dataset.elevation) > 100"
        )
        wait_camera_pitch(page, 60)
        before = camera(page)
        page.evaluate("document.querySelector('.map-canvas').__calendarIdentity = 'same-instance'")
        page.get_by_role("button", name="Semaine ISO", exact=True).click()
        expect(page.get_by_label("Année ISO")).to_have_value("2026")
        page.get_by_role("button", name="Calendrier", exact=True).click()
        ready_calendar(page, 1)
        expect(page.get_by_role("heading", name="Janvier 2027")).to_be_visible()
        expect(page.locator(".map-layer")).to_be_hidden()
        expect(page.locator(".map-attribution")).to_be_hidden()
        for date in ["2027-01-01", "2027-01-02"]:
            expect(page.locator(f'td[data-date="{date}"] .calendar-race')).to_have_count(1)
        expect(page.locator('td[data-date="2026-12-31"] .calendar-race')).to_have_count(0)
        reach_last_day(page, "2027-01-31", "Janvier 2027")
        page.screenshot(path=str(SHOTS / "desktop.png"))
        page.get_by_role("button", name="Mois précédent").click()
        ready_calendar(page, 1)
        expect(page.locator('td[data-date="2026-12-31"] .calendar-race')).to_have_count(1)
        expect(page.locator('td[data-date="2027-01-01"] .calendar-race')).to_have_count(0)
        page.get_by_role("button", name="Mois suivant").click()
        ready_calendar(page, 1)
        page.locator('td[data-date="2027-01-01"] .calendar-race').click()
        expect(page.get_by_role("heading", name=re.compile("race-mtb-multiday"))).to_be_visible()
        page.screenshot(path=str(SHOTS / "day-details.png"))
        page.get_by_label("Année civile").focus()
        page.get_by_label("Année civile").press("Tab")
        expect(page.get_by_role("heading", name=re.compile("race-mtb-multiday"))).to_be_visible()
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name="Carte", exact=True).click()
        expect(page.get_by_label("Mois")).to_have_value("1")
        expect(page.get_by_role("button", name=re.compile("Summit"))).to_have_attribute(
            "aria-pressed", "true"
        )
        wait_camera_pitch(page, 60)
        assert_camera_unchanged(camera(page), before)
        assert (
            page.evaluate("document.querySelector('.map-canvas').__calendarIdentity")
            == "same-instance"
        )
        assert_attribution_unobscured(page)


@pytest.mark.e2e
def test_calendar_shared_scope_filters_and_radius_candidates(seeded, server):
    with calendar_page(server, "candidates.png") as page:
        expect(page.locator(".result-count strong")).to_have_text("12")
        page.get_by_role("button", name="Mois", exact=True).click()
        expect(page.locator(".result-count strong")).to_have_text("11")
        page.get_by_label("Route", exact=True).check()
        page.get_by_label("open 1", exact=True).check()
        page.get_by_label("open 2", exact=True).check()
        page.get_by_role("button", name="Toutes ensemble").click()
        expect(page.locator(".result-count strong")).to_have_text("2")
        page.get_by_role("button", name="Explorer les communes").click()
        map_names = sorted(page.locator(".race-row strong").all_text_contents())
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name="Calendrier", exact=True).click()
        ready_calendar(page, 2)
        page.get_by_role("button", name=re.compile("mercredi 11 novembre 2026 · 2 courses")).click()
        assert sorted(page.locator(".race-row strong").all_text_contents()) == map_names
        page.locator(".results-panel").get_by_role(
            "button", name=re.compile("Course fictive race-road-combined")
        ).click()
        expect(page.locator(".scope .match-label")).to_have_count(1)
        expect(
            page.get_by_text("Votre admissibilité personnelle n’est pas évaluée.", exact=False)
        ).to_be_visible()
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name="Au moins une").click()
        expect(page.locator(".calendar-view")).to_have_attribute("aria-busy", "false")
        page.get_by_role("button", name="Carte", exact=True).click()
        expect(page.locator(".result-count strong")).not_to_have_text("2")
        page.get_by_role("button", name="Explorer les communes").click()
        or_names = sorted(page.locator(".race-row strong").all_text_contents())
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name="Calendrier", exact=True).click()
        expect(page.locator(".calendar-view")).to_have_attribute("aria-busy", "false")
        page.locator('td[data-date="2026-11-11"] .calendar-day').click()
        assert sorted(page.locator(".race-row strong").all_text_contents()) == or_names
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_role("button", name="Réinitialiser les filtres").click()
        ready_calendar(page, 11)
        page.locator('td[data-date="2026-11-11"] .calendar-day').click()
        expect(page.get_by_role("button", name=re.compile("race-unlocated"))).to_be_visible()
        page.get_by_role("button", name="Fermer les détails").click()
        page.get_by_label("Zone", exact=True).select_option("radius")
        # Choosing a point explicitly returns to the visible map; coordinates remain usable.
        expect(page.locator(".map-canvas")).to_be_visible()
        page.get_by_label("Longitude", exact=True).fill("0")
        page.get_by_label("Latitude", exact=True).fill("0")
        page.get_by_role("button", name="Choisir ce point").click()
        expect(page.locator(".result-count strong")).to_have_text("0")
        page.get_by_role("button", name="Calendrier", exact=True).click()
        ready_calendar(page, 0)
        expect(page.locator(".calendar-race")).to_have_count(0)
        page.get_by_role("button", name="Consulter les localisations à confirmer").click()
        page.get_by_role("button", name=re.compile("race-unlocated")).click()
        expect(page.get_by_text("cette course n’est pas comptée", exact=False)).to_be_visible()
        page.screenshot(path=str(SHOTS / "candidates.png"))


@pytest.mark.e2e
def test_calendar_mobile_dense_day_and_recoverable_error(seeded, server):
    with calendar_page(server, "mobile.png", mobile=True) as page:
        expect(page.locator(".result-count strong")).to_have_text("12")
        page.get_by_role("button", name="Calendrier", exact=True).click()
        ready_calendar(page, 11)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        reach_last_day(page, "2026-11-30", "Novembre 2026")
        page.screenshot(path=str(SHOTS / "mobile.png"))
        page.locator('td[data-date="2026-11-11"] .calendar-day').click()
        expect(page.locator(".race-row")).to_have_count(11)
        page.get_by_role("button", name=re.compile("race-cancelled")).click()
        expect(page.get_by_text("Course annulée selon la source.")).to_be_visible()
        page.get_by_role("button", name="← Retour aux courses").click()
        expect(page.locator(".race-row")).to_have_count(11)
        page.get_by_role("button", name="Fermer les détails").click()
        page.route("**/api/v1/races?*", lambda route: route.fulfill(status=503, json={}))
        page.get_by_role("button", name="Mois suivant").click()
        expect(
            page.get_by_role("heading", name="Service temporairement indisponible.")
        ).to_be_visible()
        expect(page.locator(".calendar-race")).to_have_count(0)
        page.unroute("**/api/v1/races?*")
        page.get_by_role("button", name="Réessayer", exact=True).click()
        ready_calendar(page, 1)
        expect(page.get_by_role("heading", name="Décembre 2026")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
