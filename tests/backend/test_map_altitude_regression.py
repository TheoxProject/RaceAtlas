"""Real MapView entry: Altitude no-op and full/rapid terrain mode transitions."""

import json
import re

import pytest
from browser_diagnostics import install_mobile_camera_diagnostic
from map_support import camera_diagnostic, launch
from playwright.sync_api import expect, sync_playwright
from test_accounts_ui_e2e import account_server as _account_server
from test_accounts_ui_e2e import prepare


@pytest.fixture
def account_server(database, seeded, monkeypatch):
    yield from _account_server.__wrapped__(database, seeded, monkeypatch)


def bind_engine(page):
    return page.evaluate("""() => {
        const node=document.querySelector('.map-canvas');
        let fiber=node[Object.keys(node).find(key=>key.startsWith('__reactFiber'))];
        for(let depth=0;fiber && depth<20;depth++,fiber=fiber.return) {
            let hook=fiber.memoizedState;
            for(let step=0;hook && step<100;step++,hook=hook.next) {
                const map=hook.memoizedState?.current;
                if(map && typeof map.getTerrain==='function' && typeof map.isEasing==='function') {
                    window.__altitudeRegression={map,node};return true;
                }
            }
        }
        return false;
    }""")


@pytest.mark.e2e
def test_altitude_initial_noop_and_real_and_rapid_summit_return(account_server):
    origin, _, _ = account_server
    with sync_playwright() as playwright:
        browser = launch(playwright)
        page = browser.new_page(timezone_id="Europe/Paris")
        prepare(page, mobile=True)
        try:
            install_mobile_camera_diagnostic(page)
            page.goto(origin)
            expect(page.locator(".map-canvas")).to_have_attribute(
                "data-ready", "true", timeout=20000
            )
            page.wait_for_timeout(
                650
            )  # Observe the existing500ms initial animation, not a new budget.
            initial = camera_diagnostic(page)
            assert initial.get("snapshot", {}).get("engine") is not None
            assert not any(entry["snapshot"]["engine"]["easing"] for entry in initial["trace"]), (
                "Altitude at pitch35 must not start a no-op animation"
            )
            assert bind_engine(page)
            before = page.evaluate("window.__altitudeRegression.map.getCenter().toArray()")
            # Same controlled12px resize as the ignored experiment, through the real component.
            page.evaluate("""() => {
                const {map,node}=window.__altitudeRegression;
                node.style.height=`${node.clientHeight-12}px`;map.resize();
            }""")
            page.wait_for_timeout(650)
            after = page.evaluate("window.__altitudeRegression.map.getCenter().toArray()")
            assert all(abs(a - b) <= 1e-9 for a, b in zip(before, after, strict=True))
            summit = page.get_by_role("button", name=re.compile("Summit"))
            altitude = page.get_by_role("button", name=re.compile("Altitude"))
            summit.click()
            page.wait_for_function(
                "window.__altitudeRegression.map.getPitch()===60 "
                "&& !window.__altitudeRegression.map.isEasing()"
            )
            altitude.click()
            page.wait_for_function(
                "window.__altitudeRegression.map.getPitch()===35 "
                "&& !window.__altitudeRegression.map.isEasing()"
            )
            assert page.evaluate("window.__altitudeRegression.map.getTerrain()") is None
            # MutationObserver runs after the real Summit effect, before its first RAF.
            rapid = page.evaluate("""() => new Promise((resolve,reject) => {
                const {map,node}=window.__altitudeRegression;
                const buttons=Array.from(document.querySelectorAll('.terrain-switch button'));
                const back=buttons.find(button=>button.textContent.includes('Altitude'));
                const enter=buttons.find(button=>button.textContent.includes('Summit'));
                const timeout=setTimeout(()=>{observer.disconnect();
                    reject(new Error('Rapid transition not observed'));},5000);
                const observer=new MutationObserver(()=>{
                    if(node.dataset.terrain!=='summit')return;
                    observer.disconnect();clearTimeout(timeout);
                    const state={pitch:map.getPitch(),easing:map.isEasing()};
                    back.click();resolve(state);
                });
                observer.observe(node,{attributes:true,attributeFilter:['data-terrain']});
                enter.click();
            })""")
            assert rapid == {"pitch": 35, "easing": True}, (
                "Rapid case must actually precede the first frame"
            )
            expect(altitude).to_have_attribute("aria-pressed", "true")
            page.wait_for_function(
                "window.__altitudeRegression.map.getPitch()===35 "
                "&& !window.__altitudeRegression.map.isEasing()"
            )
            assert page.evaluate("window.__altitudeRegression.map.getTerrain()") is None
            print(
                "ALTITUDE_REGRESSION "
                + json.dumps(
                    {
                        "initial_no_easing": True,
                        "resize_before": before,
                        "resize_after": after,
                        "rapid_entry": rapid,
                    }
                )
            )
        except Exception:
            print("ALTITUDE_REGRESSION_CACHE " + json.dumps(camera_diagnostic(page)))
            raise
        finally:
            browser.close()
