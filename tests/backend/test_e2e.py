import threading

import pytest
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import text
from werkzeug.serving import make_server

from raceatlas import create_app


@pytest.fixture()
def server(app):
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)


@pytest.mark.e2e
def test_compiled_react_flask_postgresql(seeded, server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(server)
        expect(
            page.get_by_role("heading", name="Course fictive race-access-ambiguous")
        ).to_be_visible()
        expect(page.get_by_text("Épreuve lue depuis PostgreSQL", exact=False)).to_be_visible()
        seeded.execute(
            text(
                "UPDATE race SET name = 'Épreuve modifiée dans PostgreSQL' "
                "WHERE id = 'race-access-ambiguous'"
            )
        )
        seeded.commit()
        with page.expect_response("**/api/v1/races/race-access-ambiguous") as response:
            page.get_by_role("button", name="Actualiser la démonstration").click()
        assert response.value.status == 200
        expect(page.get_by_role("heading", name="Épreuve modifiée dans PostgreSQL")).to_be_visible()
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert not errors
        browser.close()


@pytest.mark.e2e
def test_compiled_empty_database(session, server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(server)
        expect(page.get_by_role("heading", name="Aucune épreuve de démonstration")).to_be_visible()
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
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{server.server_port}")
            expect(page.get_by_role("alert")).to_contain_text("Service temporairement indisponible")
            assert "private" not in page.content()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        app.extensions["database"].dispose()
