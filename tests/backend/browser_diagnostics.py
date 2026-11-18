"""Bounded public-only browser diagnostics; never add waits or inspect private traffic bodies."""

import json
import time
from urllib.parse import parse_qs, urlsplit

from map_support import camera_diagnostic


class PublicTransportDiagnostic:
    """Compare CDP transport events to Playwright callbacks, not their underlying cause."""

    def __init__(self, page, classify, trace, *, callbacks=False, emit=True):
        self.page, self.classify, self.trace = page, classify, trace
        self.started = time.monotonic()
        self.emit = emit
        self.requests, self.browser_requests = {}, {}
        self.browser_start = None
        self.session = None
        self.callbacks = (
            {
                "request": lambda request: self.record_callback(request, "request"),
                "response": lambda response: self.record_callback(
                    response.request, "response", response.status
                ),
                "requestfinished": lambda request: self.record_callback(request, "finished"),
                "requestfailed": lambda request: self.record_callback(request, "failed"),
            }
            if callbacks
            else {}
        )
        trace["transport"] = []

    def event(self, origin, kind, phase, number, **metadata):
        events = self.trace["transport"]
        if len(events) < 96:
            events.append(
                {
                    "origin": origin,
                    "kind": kind,
                    "phase": phase,
                    "request_id": number,
                    "host_ms": round((time.monotonic() - self.started) * 1000, 2),
                    **metadata,
                }
            )

    def record_callback(self, request, phase, status=None):
        entry = self.requests.get(request)
        if entry is None:
            kind = self.classify(request.url)
            if kind is None or len(self.requests) >= 12:
                return
            entry = self.requests[request] = (kind, len(self.requests) + 1)
        self.event("playwright", entry[0], phase, entry[1], status=status)

    def browser_event(self, phase, payload):
        identifier = payload.get("requestId")
        entry = self.browser_requests.get(identifier)
        if phase == "request" and entry is None:
            kind = self.classify(payload.get("request", {}).get("url", ""))
            if kind is None or len(self.browser_requests) >= 12:
                return
            entry = self.browser_requests[identifier] = (kind, len(self.browser_requests) + 1)
        if entry is None:
            return
        metadata = {}
        stamp = payload.get("timestamp")
        if isinstance(stamp, (int, float)):
            if self.browser_start is None:
                self.browser_start = stamp
            metadata["browser_ms"] = round((stamp - self.browser_start) * 1000, 2)
        if phase == "response":
            metadata["status"] = payload.get("response", {}).get("status")
        if phase == "finished":
            metadata["encoded_bytes"] = payload.get("encodedDataLength")
        if phase == "failed":
            metadata["cancelled"] = bool(payload.get("canceled"))
        self.event("cdp", entry[0], phase, entry[1], **metadata)

    def mark(self, phase):
        self.trace["phase"] = phase
        self.event("host", "selection", phase, None)

    def __enter__(self):
        for event, callback in self.callbacks.items():
            self.page.on(event, callback)
        try:
            self.session = self.page.context.new_cdp_session(self.page)
            for event, phase in (
                ("requestWillBeSent", "request"),
                ("responseReceived", "response"),
                ("loadingFinished", "finished"),
                ("loadingFailed", "failed"),
            ):
                self.session.on(
                    "Network." + event,
                    lambda payload, phase=phase: self.browser_event(phase, payload),
                )
            self.session.send("Network.enable")
            self.trace["cdp"] = "armed"
        except Exception as error:
            # Diagnostics cannot replace a test assertion with a driver setup failure.
            self.trace["cdp"] = "unavailable-" + type(error).__name__
        return self

    def __exit__(self, kind, error, traceback):
        if kind is not None:
            self.trace["error_type"] = kind.__name__
            self.trace["camera"] = camera_diagnostic(self.page)  # Host cache only.
        for event, callback in self.callbacks.items():
            self.page.remove_listener(event, callback)
        self.trace["elapsed_ms"] = round((time.monotonic() - self.started) * 1000, 2)
        if self.emit:
            print("PUBLIC_TRANSPORT_DIAGNOSTIC " + json.dumps(self.trace))
        # On failure leave browser-session cleanup to the test's existing browser.close.
        # Reading/printing cached evidence must not first depend on a responsive driver.
        if self.session is not None and "error_type" not in self.trace:
            try:
                self.session.detach()
            except Exception:
                pass  # Cleanup cannot replace the original result or leak driver messages.


def public_search_kind(url, query):
    """Same known synthetic Road/November selection, with no retained URL or query text."""
    parsed = urlsplit(url)
    if parsed.path not in {"/api/v1/races", "/api/v1/map"}:
        return None
    parameters = parse_qs(parsed.query)
    try:
        selected = json.loads(parameters.get("filter", [""])[0])
    except (ValueError, TypeError):
        return None
    if (
        not isinstance(selected, dict)
        or selected.get("query") != query
        or selected.get("from") != "2026-11-01"
        or selected.get("to") != "2026-11-30"
        or selected.get("disciplines") != ["road"]
    ):
        return None
    return {
        ("/api/v1/races", ("200",)): "races",
        ("/api/v1/map", ("200",)): "map",
        ("/api/v1/races", ("1",)): "witness",
    }.get((parsed.path, tuple(parameters.get("limit", []))))


def camera_phase(page, phase):
    """Record action boundary in the host cache without asking the engine/renderer anything."""
    events = page._raceatlas_mobile_phases
    events.append(
        {
            "phase": phase,
            "host_ms": time.monotonic() * 1000,
            "cached_camera": page._raceatlas_camera_latest.get("snapshot"),
            "cached_host_received_ms": page._raceatlas_camera_latest.get("host_received_ms"),
        }
    )
    del events[:-12]
    page._raceatlas_camera_latest["action_phases"] = list(events)
    page._raceatlas_mobile_phase = phase


def install_mobile_camera_diagnostic(page):
    """Arm before navigation; passively discover the map without wrapping engine methods."""
    page._raceatlas_camera_latest = {"unavailable": "not-attached", "trace": []}
    page._raceatlas_mobile_phase = "before-navigation"
    page._raceatlas_mobile_phases = []

    def receive(_source, payload):
        payload["host_received_ms"] = time.monotonic() * 1000
        payload["host_phase"] = page._raceatlas_mobile_phase
        payload["action_phases"] = list(page._raceatlas_mobile_phases)
        page._raceatlas_camera_latest = payload

    page.expose_binding("__raceatlasMobileCameraSnapshot", receive)
    page.add_init_script("""(() => {
        let attached = false, lastSample = -Infinity;
        const trace = [];
        const attach = () => {
            if (attached) return;
            const node = document.querySelector('.map-canvas');
            if (!node) return;
            const key = Object.keys(node).find(key => key.startsWith('__reactFiber'));
            let fiber = node[key], map;
            for (let depth = 0; fiber && depth < 20 && !map; depth++, fiber = fiber.return) {
                let hook = fiber.memoizedState;
                for (let step = 0; hook && step < 100; step++, hook = hook.next) {
                    const candidate = hook.memoizedState?.current;
                    if (candidate && typeof candidate.getPitch === 'function'
                        && typeof candidate.getTerrain === 'function') { map = candidate; break; }
                }
            }
            if (!map) return;
            attached = true; observer.disconnect();
            const state = () => ({performance_ms: performance.now(),
                engine: {center: map.getCenter().toArray(), zoom: map.getZoom(),
                    bearing: map.getBearing(), pitch: map.getPitch(),
                    moving: map.isMoving(), easing: map.isEasing()},
                dom: {camera: JSON.parse(node.dataset.camera || 'null'),
                    ready: node.dataset.ready, width: node.clientWidth, height: node.clientHeight},
                viewport: {width: innerWidth, height: innerHeight,
                    visual_width: visualViewport?.width, visual_height: visualViewport?.height,
                    scroll_x: scrollX, scroll_y: scrollY}});
            const record = (kind, event) => {
                try {
                    const now = performance.now();
                    if ((kind === 'move' || kind === 'scroll') && now - lastSample < 100) return;
                    lastSample = now;
                    const original = event?.originalEvent || event;
                    const entry = {kind, performance_ms: now, snapshot: state(),
                        original_type: original?.type,
                        trusted: original?.isTrusted === true,
                        target_is_map: !!(original?.target instanceof Node
                            && node.contains(original.target))};
                    trace.push(entry); if (trace.length > 40) trace.shift();
                    window.__raceatlasMobileCameraSnapshot({snapshot: entry.snapshot,
                        trace: trace.slice()}).catch(() => {});
                } catch { /* Metadata must not interrupt the normal event path. */ }
            };
            for (const type of ['movestart', 'move', 'moveend', 'resize', 'idle']) {
                map.on(type, event => record(type, event));
            }
            for (const type of ['pointerdown', 'pointerup', 'touchstart', 'touchend',
                'wheel', 'keydown', 'scroll', 'resize']) {
                window.addEventListener(type, event => record(type, event),
                    {passive: true, capture: true});
            }
            visualViewport?.addEventListener('resize', event => record('visual-resize', event));
            record('attached');
        };
        const observer = new MutationObserver(attach);
        const start = () => {
            observer.observe(document.documentElement, {childList: true, subtree: true,
                attributes: true, attributeFilter: ['class', 'data-ready']});
            attach();
        };
        if (document.documentElement) start();
        else document.addEventListener('DOMContentLoaded', start, {once: true});
    })();""")
    camera_phase(page, "before-navigation")
