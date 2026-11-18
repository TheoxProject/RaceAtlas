"""Real offline synchronization -> compiled React/Flask/PG, no debug endpoint."""

import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import test_sync as source
from browser_diagnostics import (
    PublicTransportDiagnostic,
    camera_phase,
    install_mobile_camera_diagnostic,
    public_search_kind,
)
from map_support import (
    camera,
    camera_diagnostic,
    install_camera_diagnostic,
    launch,
    limit_software_map_framebuffer,
)
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_accounts_ui_e2e import account, prepare, select_public_month, sign_in
from test_accounts_ui_e2e import account_server as _account_server
from test_accounts_ui_e2e import admission_clock as _admission_clock
from test_auth_http_sessions import PASSWORD, identity
from test_e2e import assert_camera_unchanged, open_discipline_picker, wait_camera_pitch
from test_private_planning import isolation as isolation

from raceatlas.models import PersonalNotification, Race, SavedEntry, SourceRecord, SourceRevision
from raceatlas.sync import synchronize

SHOTS = Path(__file__).resolve().parents[2] / ".local-tools" / "notifications-ui-screenshots"
PREFIX = "Source notifications fictive"
ALICE, BOB = "notifications-alice@example.test", "notifications-bob@example.test"


@pytest.fixture
def admission_clock(monkeypatch):
    yield from _admission_clock.__wrapped__(monkeypatch)


@pytest.fixture
def account_server(database, seeded, monkeypatch):
    yield from _account_server.__wrapped__(database, seeded, monkeypatch)


def imported_source(database):
    observed = replace(source.observation("NOTIFICATIONS_UI"), name=PREFIX)
    assert (
        synchronize(database, [source.batch(observed)], checked_at=source.NOW).status == "success"
    )
    with Session(database) as session:
        race = session.scalar(
            select(Race)
            .join(SourceRecord)
            .where(
                SourceRecord.provider == "ffc",
                SourceRecord.source_season == observed.key.season,
                SourceRecord.race_number == observed.key.race_number,
            )
        )
        assert race is not None
        by_label = {scope.raw_label: scope for scope in race.scopes}
        assert set(by_label) == {scope.raw_label for scope in observed.scopes}
        for expected in observed.scopes:
            actual = by_label[expected.raw_label]
            assert actual.source_list_id is expected.source_list_id is None
            assert actual.identity_status == expected.identity_status == "unverified"
            assert (
                actual.kind == expected.kind
                and actual.eligibility_status == expected.eligibility_status
            )
            assert {
                tuple(sorted(item.category_code for item in rule.categories))
                for rule in actual.rules
            } == {tuple(sorted(rule.category_codes)) for rule in expected.rules}
        scopes = {label: scope.id for label, scope in by_label.items()}
        return observed, race.id, scopes


def changed_source(database, original, revision):
    checked = source.NOW + timedelta(minutes=revision)
    observation = replace(
        original,
        name=f"{PREFIX} — changement {revision}",
        start_date=original.start_date + timedelta(days=revision % 2),
        end_date=original.end_date + timedelta(days=revision % 2),
        checked_at=checked,
    )
    result = synchronize(database, [source.batch(observation, checked=checked)], checked_at=checked)
    assert result.status == "success" and result.missing_marked == 0
    return observation


def capture(page, name):
    assert not urlsplit(page.url).fragment, "Private fragment must be scrubbed"
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.locator("#notifications-title").evaluate("node=>node.scrollIntoView({block:'start'})")
    page.screenshot(path=str(SHOTS / name), timeout=5000)


def capture_failure(page, name):
    try:
        SHOTS.mkdir(parents=True, exist_ok=True)
        if not urlsplit(page.url).fragment:
            page.screenshot(path=str(SHOTS / name), timeout=5000)
    except Exception:
        pass  # Never replace the original assertion/transport/camera diagnostic.


def open_source_map(page, origin):
    page.goto(origin)
    expect(page.locator(".map-canvas")).to_have_attribute("data-ready", "true", timeout=20000)
    page.get_by_role("button", name="Mois", exact=True).click()
    page.get_by_label("Mois", exact=True).select_option("11")
    open_discipline_picker(page)
    page.get_by_label("Route", exact=True).check()
    page.get_by_placeholder("Course, commune ou club…").fill(PREFIX)
    expect(page.locator(".result-count strong")).to_have_text("1", timeout=15000)
    page.get_by_role("button", name="Explorer les communes", exact=True).click()
    page.locator(".race-row").filter(has_text=PREFIX).click()


def source_scope(page, scope_id):
    return page.locator(f'.scope-save[data-scope-id="{scope_id}"]')


def save(page, scope_id, status, label):
    scope = source_scope(page, scope_id)
    scope.get_by_label("Votre statut pour cette liste").scroll_into_view_if_needed()
    scope.get_by_label("Votre statut pour cette liste").select_option(status)
    scope.get_by_role("button", name="Sauvegarder cette liste", exact=True).click()
    expect(scope.locator(".scope-saved")).to_have_text("Sauvegardée : " + label)


def season(page, count):
    account(page)
    page.get_by_role("button", name="Ma saison", exact=True).click()
    expect(page.locator(".notifications-panel")).to_have_attribute("aria-busy", "false")
    expect(
        page.locator(".notifications-panel").get_by_text(
            f"{count} nouveauté" + ("s" if count != 1 else ""), exact=True
        )
    ).to_be_visible()


def refresh_changes(page, count):
    page.get_by_role("button", name="Actualiser les changements", exact=True).click()
    expect(
        page.locator(".notifications-panel").get_by_text(
            f"{count} nouveauté" + ("s" if count != 1 else ""), exact=True
        )
    ).to_be_visible()
    expect(
        page.get_by_role("button", name="Actualiser les changements", exact=True)
    ).to_be_enabled()


def close_account(page):
    page.keyboard.press("Escape")
    expect(page.get_by_role("button", name="Compte", exact=True)).to_be_focused()


def remove_named_scope(page, label, remaining_count):
    page.locator(".season-row").filter(has_text=label).click()
    expect(page.locator(".season-detail .scope")).to_have_count(1)
    page.get_by_role("button", name="Retirer cette sauvegarde", exact=True).click()
    expect(
        page.locator(".notifications-panel").get_by_text(
            f"{remaining_count} nouveauté" + ("s" if remaining_count != 1 else ""), exact=True
        )
    ).to_be_visible()


@pytest.mark.e2e
def test_notifications_real_sync_offpage_ack_two_actors_scope_readd_desktop(
    admission_clock, account_server, database
):
    origin, _, _ = account_server
    original, race_id, scopes = imported_source(database)
    one, two = (
        next(value for label, value in scopes.items() if label.startswith(prefix + ";"))
        for prefix in ("Liste fictive A", "Liste fictive B")
    )
    alice, bob = identity(database, ALICE), identity(database, BOB)
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris")
        other = browser.new_page(timezone_id="Europe/Paris")
        prepare(page)
        prepare(other)
        try:
            open_source_map(page, origin)
            page.get_by_role("button", name="Fermer les détails", exact=True).click()
            limit_software_map_framebuffer(page)
            assert install_camera_diagnostic(page) and "snapshot" in camera_diagnostic(page)
            page.get_by_role("button", name="Summit", exact=False).click()
            wait_camera_pitch(page, 60)
            page.wait_for_function(
                "Number(document.querySelector('.map-canvas').dataset.elevation)>100", timeout=10000
            )
            page.locator(".maplibregl-ctrl-zoom-in").click()
            page.wait_for_function(
                "JSON.parse(document.querySelector('.map-canvas').dataset.camera).zoom===7.5"
            )
            before, node = camera(page), page.locator(".map-canvas").element_handle()
            page.get_by_role("button", name="Explorer les communes", exact=True).click()
            page.locator(".race-row").filter(has_text=PREFIX).click()
            page.locator(".race-detail .scope").filter(has_text="Liste fictive A").get_by_role(
                "button", name="Se connecter pour sauvegarder cette liste", exact=True
            ).click()
            sign_in(page, ALICE, PASSWORD)
            close_account(page)
            save(page, one, "planned", "Prévue")
            save(page, two, "registered", "Inscrit")
            with Session(database) as session:
                old_save = session.scalar(
                    select(SavedEntry.id).where(
                        SavedEntry.account_id == alice, SavedEntry.scope_id == one
                    )
                )
            admission_clock.advance(61)  # Deliberate phase boundary, no policy/CSRF clock change.
            open_source_map(other, origin)
            other.locator(".race-detail .scope").filter(has_text="Liste fictive B").get_by_role(
                "button", name="Se connecter pour sauvegarder cette liste", exact=True
            ).click()
            sign_in(other, BOB, PASSWORD)
            close_account(other)
            save(other, two, "interested", "Intéressé")
            admission_clock.advance(61)
            # All52 notifications come from26 real, committed sync runs. No PN
            # fixture insertion or fake message endpoint participates.
            for revision in range(1, 27):
                changed_source(database, original, revision)
            page.get_by_role("button", name="← Retour aux courses", exact=True).click()
            with PublicTransportDiagnostic(
                page,
                lambda url: public_search_kind(url, "race-road-split"),
                {"selection": "road-split-search"},
                callbacks=True,
            ) as diagnostic:
                diagnostic.mark("search-action")
                page.get_by_placeholder("Course, commune ou club…").fill("race-road-split")
                diagnostic.mark("presentation")
                expect(page.locator(".result-count strong")).to_have_text("1", timeout=15000)
                diagnostic.mark("ready")
            select_public_month(page, "1", [])
            season(page, 52)
            expect(page.locator(".notification-card")).to_have_count(50)
            expect(
                page.locator(".notification-card").get_by_text("Liste fictive A", exact=False).first
            ).to_be_visible()
            expect(
                page.locator(".notification-card").get_by_text("Liste fictive B", exact=False).first
            ).to_be_visible()
            expect(
                page.locator(".notification-card").first.get_by_text("Nom", exact=True)
            ).to_be_visible()
            capture(page, "desktop.png")
            page.get_by_role("button", name="Marquer comme lues", exact=True).click()
            expect(
                page.locator(".notifications-panel").get_by_text("0 nouveautés", exact=True)
            ).to_be_visible()
            with Session(database) as session:
                assert (
                    session.scalar(
                        select(func.count())
                        .select_from(PersonalNotification)
                        .where(
                            PersonalNotification.account_id == alice,
                            PersonalNotification.read_at.is_not(None),
                        )
                    )
                    == 52
                )
            season(other, 26)
            admission_clock.advance(61)
            changed_source(database, original, 27)
            refresh_changes(page, 2)
            refresh_changes(other, 27)
            remove_named_scope(page, "Liste fictive A", 1)
            with Session(database) as session:
                assert (
                    session.scalar(
                        select(func.count())
                        .select_from(PersonalNotification)
                        .where(
                            PersonalNotification.account_id == alice,
                            PersonalNotification.scope_id == one,
                        )
                    )
                    == 0
                )
                assert (
                    session.scalar(
                        select(SavedEntry.id).where(
                            SavedEntry.account_id == bob, SavedEntry.scope_id == two
                        )
                    )
                    is not None
                )
            close_account(page)
            select_public_month(page, "11", ["race-road-split"])
            page.get_by_placeholder("Course, commune ou club…").fill(PREFIX)
            expect(page.locator(".result-count strong")).to_have_text("1", timeout=15000)
            if not page.locator(".results-panel").is_visible():
                page.get_by_role("button", name="Explorer les communes", exact=True).click()
            page.locator(".race-row").filter(has_text=PREFIX).click()
            admission_clock.advance(61)
            save(page, one, "planned", "Prévue")
            with Session(database) as session:
                replacement = session.scalar(
                    select(SavedEntry).where(
                        SavedEntry.account_id == alice, SavedEntry.scope_id == one
                    )
                )
                assert replacement.id != old_save and replacement.notifications_after_sequence == 27
                assert {
                    scope.raw_label: scope.id for scope in session.get(Race, race_id).scopes
                } == scopes
            with PublicTransportDiagnostic(
                page,
                lambda url: public_search_kind(url, "race-road-split"),
                {"selection": "road-split-search"},
                callbacks=True,
            ) as diagnostic:
                diagnostic.mark("search-action")
                page.get_by_placeholder("Course, commune ou club…").fill("race-road-split")
                diagnostic.mark("presentation")
                expect(page.locator(".result-count strong")).to_have_text("1", timeout=15000)
                diagnostic.mark("ready")
            select_public_month(page, "1", [])
            season(page, 1)
            changed_source(database, original, 28)
            refresh_changes(page, 3)
            one_cards = page.locator(".notification-card").filter(has_text="Liste fictive A")
            expect(one_cards).to_have_count(1)
            expect(one_cards.get_by_text("Non lue", exact=True)).to_be_visible()
            close_account(page)
            assert node.evaluate("node=>node===document.querySelector('.map-canvas')")
            assert_camera_unchanged(camera(page), before)
            expect(page.get_by_label("Mois", exact=True)).to_have_value("1")
            expect(page.get_by_label("Route", exact=True)).to_be_checked()
            expect(page.get_by_placeholder("Course, commune ou club…")).to_have_value(
                "race-road-split"
            )
        except Exception:
            capture_failure(page, "desktop.png")
            raise
        finally:
            browser.close()


@pytest.mark.e2e
def test_notifications_calendar_presence_ack_and_mobile_keyboard(
    admission_clock, account_server, database
):
    origin, _, _ = account_server
    original, race_id, scopes = imported_source(database)
    one, two = (
        next(value for label, value in scopes.items() if label.startswith(prefix + ";"))
        for prefix in ("Liste fictive A", "Liste fictive B")
    )
    identity(database, ALICE)
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris")
        prepare(page, mobile=True)
        try:
            install_mobile_camera_diagnostic(page)
            camera_phase(page, "navigation")
            page.goto(origin)
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            camera_phase(page, "initial-ready-before-baseline")
            node, before = page.locator(".map-canvas").element_handle(), camera(page)
            camera_phase(page, "filters")
            page.get_by_role("button", name="☷ Filtres", exact=True).click()
            open_discipline_picker(page)
            page.get_by_label("Route", exact=True).check()
            page.get_by_placeholder("Course, commune ou club…").fill(PREFIX)
            page.get_by_role("button", name="Voir les courses sur la carte", exact=True).click()
            camera_phase(page, "calendar")
            page.get_by_role("button", name="Calendrier", exact=True).click()
            expect(page.locator(".calendar-view")).to_have_attribute("aria-busy", "false")
            page.locator('td[data-date="2026-11-11"] .calendar-day').click()
            page.locator(".race-row").filter(has_text=PREFIX).click()
            page.locator(".race-detail .scope").filter(has_text="Liste fictive A").get_by_role(
                "button", name="Se connecter pour sauvegarder cette liste", exact=True
            ).click()
            camera_phase(page, "account-dialog")
            sign_in(page, ALICE, PASSWORD)
            close_account(page)
            save(page, one, "interested", "Intéressé")
            save(page, two, "completed", "Terminée")
            page.get_by_role("button", name="Fermer les détails", exact=True).click()
            camera_phase(page, "calendar-scroll-next-month")
            page.get_by_role("button", name="Mois suivant", exact=True).scroll_into_view_if_needed()
            page.get_by_role("button", name="Mois suivant", exact=True).click()
            expect(page.get_by_role("heading", name="Décembre 2026", exact=True)).to_be_visible()
            expect(page.locator(".calendar-view")).to_have_attribute("aria-busy", "false")
            admission_clock.advance(61)
            absent = source.NOW + timedelta(hours=1)
            result = synchronize(
                database, [source.batch(keys=(), checked=absent)], checked_at=absent
            )
            assert result.status == "success" and result.missing_marked == 1
            camera_phase(page, "notifications-dialog")
            season(page, 2)
            expect(page.locator(".notification-card")).to_have_count(2)
            expect(
                page.locator(".notification-card").get_by_text(
                    "Après : Présence à vérifier (absence ne signifie pas annulation)", exact=True
                )
            ).to_have_count(2)
            expect(
                page.locator(".notification-card").get_by_text(
                    "Annulée selon la source", exact=True
                )
            ).to_have_count(0)
            capture(page, "mobile.png")
            mark = page.get_by_role("button", name="Marquer comme lues", exact=True)
            camera_phase(page, "notification-scroll-keyboard")
            mark.scroll_into_view_if_needed()
            mark.focus()
            page.keyboard.press("Enter")
            expect(
                page.locator(".notifications-panel").get_by_text("0 nouveautés", exact=True)
            ).to_be_visible()
            returned = absent + timedelta(hours=1)
            restored = replace(original, checked_at=returned)
            assert (
                synchronize(
                    database, [source.batch(restored, checked=returned)], checked_at=returned
                ).status
                == "success"
            )
            refresh_changes(page, 2)
            expect(
                page.locator(".notification-card").get_by_text(
                    "Après : Présente dans la source", exact=True
                )
            ).to_have_count(2)
            expect(page.locator(".notification-card")).to_have_count(4)
            last = page.locator(".notification-card").last
            last.scroll_into_view_if_needed()
            expect(last).to_be_visible()
            assert page.locator("dialog.account-dialog").evaluate(
                "node=>node.scrollWidth<=node.clientWidth+1"
            )
            camera_phase(page, "dialog-tab")
            page.keyboard.press("Tab")
            assert page.locator("dialog.account-dialog").evaluate(
                "node=>node.contains(document.activeElement)"
            )
            admission_clock.advance(61)
            remove_named_scope(page, "Liste fictive A", 1)
            expect(
                page.locator(".notification-card").get_by_text("Liste fictive A", exact=False)
            ).to_have_count(0)
            expect(
                page.locator(".notification-card").get_by_text("Liste fictive B", exact=False)
            ).to_have_count(2)
            with Session(database) as session:
                race = session.get(Race, race_id)
                assert race.status == "scheduled" and race.source_presence == "present"
                assert (
                    session.scalar(
                        select(func.count())
                        .select_from(SourceRevision)
                        .where(SourceRevision.race_id == race_id)
                    )
                    == 1
                )
                assert {scope.raw_label: scope.id for scope in race.scopes} == scopes
            close_account(page)
            expect(page.get_by_role("heading", name="Décembre 2026", exact=True)).to_be_visible()
            assert node.evaluate("node=>node===document.querySelector('.map-canvas')")
            camera_phase(page, "final-camera-assertion")
            assert_camera_unchanged(camera(page), before)
            camera_phase(page, "filters")
            page.get_by_role("button", name="☷ Filtres", exact=True).click()
            expect(page.get_by_placeholder("Course, commune ou club…")).to_have_value(PREFIX)
            expect(page.get_by_label("Route", exact=True)).to_be_checked()
        except Exception:
            print("MOBILE_CAMERA_DIAGNOSTIC " + json.dumps(camera_diagnostic(page)))
            capture_failure(page, "mobile.png")
            raise
        else:
            print("MOBILE_CAMERA_DIAGNOSTIC " + json.dumps(camera_diagnostic(page)))
        finally:
            browser.close()
