"""Deterministic synthetic map resources; real MapLibre/Chromium WebGL remains active."""

import json
import math
import struct
import time
import zlib

STYLE_URL = "https://tiles.openfreemap.org/styles/liberty"
DEM_URL = "https://tiles.mapterhorn.com/tilejson.json"


def terrain_png():
    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload))
        )

    rows = bytearray()
    for y in range(512):
        rows.append(0)
        for x in range(512):
            elevation = int(32768 + 600 + 400 * math.sin(x / 80) * math.cos(y / 80))
            rows.extend((elevation // 256, elevation % 256, 0, 255))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 512, 512, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def offline_style():
    lines = []
    for index in range(22):
        lines.append(
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [2 + step / 20, 43.5 + index / 12 + math.sin(step / 13 + index / 3) / 6]
                        for step in range(100)
                    ],
                },
            }
        )
    return {
        "version": 8,
        "sources": {
            "synthetic-contours": {
                "type": "geojson",
                "data": {"type": "FeatureCollection", "features": lines},
            }
        },
        "layers": [
            {"id": "background", "type": "background", "paint": {"background-color": "#e7eddf"}},
            {
                "id": "contours",
                "type": "line",
                "source": "synthetic-contours",
                "paint": {"line-color": "#b6c6ac", "line-width": 1.1},
            },
        ],
    }


def intercept_map(page, *, dem_failure=False, base_failure=False, base_pending=False):
    style = offline_style()
    pending = []
    if base_failure or base_pending:
        style["sources"]["missing-base"] = {
            "type": "raster",
            "tileSize": 256,
            "tiles": ["https://tiles.openfreemap.org/synthetic/{z}/{x}/{y}.png"],
        }
        style["layers"].append({"id": "missing-base", "type": "raster", "source": "missing-base"})
        page.route(
            "https://tiles.openfreemap.org/synthetic/**",
            (lambda route: pending.append(route))
            if base_pending
            else lambda route: route.fulfill(status=503, body="offline"),
        )
    page.route(STYLE_URL, lambda route: route.fulfill(json=style))
    page.route(
        DEM_URL,
        lambda route: route.fulfill(status=503, body="offline")
        if dem_failure
        else route.fulfill(
            json={
                "tilejson": "3.0.0",
                "tiles": ["https://tiles.mapterhorn.com/synthetic/{z}/{x}/{y}.png"],
                "minzoom": 0,
                "maxzoom": 0,
                "encoding": "terrarium",
                "tileSize": 512,
            }
        ),
    )
    tile = terrain_png()
    page.route(
        "https://tiles.mapterhorn.com/synthetic/**",
        lambda route: route.fulfill(body=tile, content_type="image/png"),
    )
    # Any unexpected external style dependency fails locally rather than accessing providers.
    page.route("https://tiles.openfreemap.org/planet/**", lambda route: route.abort())
    return pending


def camera(page):
    return json.loads(page.locator(".map-canvas").get_attribute("data-camera"))


def install_camera_diagnostic(page):
    """Read the pinned React engine ref for diagnostics only; never change map behavior."""
    counts = {"console_error": 0, "console_warning": 0, "gpu_stall": 0, "pageerror": 0}

    def console(message):
        if message.type in {"error", "warning"}:
            counts["console_" + message.type] += 1
        if "GPU stall" in message.text:
            counts["gpu_stall"] += 1

    def pageerror(_error):
        counts["pageerror"] += 1

    page.on("console", console)
    page.on("pageerror", pageerror)
    page._raceatlas_camera_counts = counts

    def receive(_source, payload):
        payload["host_received_ms"] = time.monotonic() * 1000
        page._raceatlas_camera_latest = payload

    page.expose_binding("__raceatlasCameraSnapshot", receive)
    return page.evaluate("""() => {
        const node = document.querySelector('.map-canvas');
        const key = Object.keys(node).find(key => key.startsWith('__reactFiber'));
        let fiber = node[key], map;
        for (let depth = 0; fiber && depth < 20 && !map; depth++, fiber = fiber.return) {
            let hook = fiber.memoizedState;
            for (let step = 0; hook && step < 100; step++, hook = hook.next) {
                const candidate = hook.memoizedState?.current;
                if (candidate && typeof candidate.getPitch === 'function'
                    && typeof candidate.getTerrain === 'function') {
                    map = candidate;
                    break;
                }
            }
        }
        const trace = [], stops = [], contexts = {lost: 0, restored: 0};
        let frames = 0, lastFrameSample = -Infinity;
        const state = () => ({
            performance_ms: performance.now(), date_ms: Date.now(),
            render_frames: frames,
            reduced_motion: matchMedia('(prefers-reduced-motion: reduce)').matches,
            engine: map ? {
                pitch: map.getPitch(), center: map.getCenter().toArray(),
                zoom: map.getZoom(), bearing: map.getBearing(),
                terrain: map.getTerrain(), elevation: map.queryTerrainElevation(map.getCenter()),
                moving: map.isMoving(), easing: map.isEasing(),
                ease_frame: map._easeFrameId ?? null,
                ease_elapsed_ms: performance.now() - map._easeStart,
                render_frame: !!map._frame, loaded: map._loaded,
                style_loaded: map.style?.loaded(),
                context_lost: node.querySelector('canvas')?.getContext('webgl2')?.isContextLost()
            } : null,
            dom: {
                camera: JSON.parse(node.dataset.camera || 'null'),
                mode: node.dataset.terrain, elevation: node.dataset.elevation,
                warning: document.querySelector('.map-warning')?.textContent?.slice(0, 250),
                modes: Array.from(document.querySelectorAll('.terrain-switch button'))
                    .map(button => ({pressed: button.getAttribute('aria-pressed'),
                        disabled: button.disabled}))
            },
            contexts: {...contexts}
        });
        const record = (kind, extra = {}) => {
            try {
                const entry = {kind, ms: performance.now(), pitch: map.getPitch(),
                    moving: map.isMoving(), easing: map.isEasing(), ...extra};
                trace.push(entry);
                if (trace.length > 60) trace.shift();
                if (kind === 'stop' || kind === '_stop') {
                    stops.push(entry);
                    if (stops.length > 12) stops.shift();
                }
                window.__raceatlasCameraSnapshot({snapshot: state(),
                    trace: trace.slice(), stops: stops.slice()}).catch(() => {});
            } catch {
                // Diagnostics must not interrupt the engine or its normal event handlers.
            }
        };
        if (map) {
            for (const type of ['movestart', 'moveend', 'pitchstart', 'pitchend',
                'terrain', 'error', 'resize', 'webglcontextlost', 'webglcontextrestored']) {
                map.on(type, event => {
                    if (type === 'webglcontextlost') contexts.lost++;
                    if (type === 'webglcontextrestored') contexts.restored++;
                    record(type, {source: event.sourceId?.slice(0, 60),
                        error_status: event.error?.status,
                        error_mentions_dem: !!event.error?.message?.includes('mapterhorn')});
                });
            }
            for (const name of ['stop', '_stop']) {
                const original = map[name];
                map[name] = function(...args) {
                    const stack = new Error().stack.split('\\n').slice(2, 5)
                        .map(line => line.replace(/https?:\\/\\/\\S+/g, '[asset]').slice(0, 130));
                    record(name, {stack});
                    return original.apply(this, args);
                };
            }
            map.on('render', () => {
                frames++;
                const now = performance.now();
                if (frames <= 3 || now - lastFrameSample >= 250 || frames % 30 === 0) {
                    lastFrameSample = now;
                    record('frame');
                }
            });
            record('installed');
        }
        window.__raceatlasCameraDiagnostic = {state, trace};
        return !!map;
    }""")


def camera_diagnostic(page):
    """Use host-cached metadata even if the renderer no longer responds to JavaScript."""
    diagnostic = dict(
        getattr(page, "_raceatlas_camera_latest", {"unavailable": "no-snapshot", "trace": []})
    )
    diagnostic["host_capture_ms"] = time.monotonic() * 1000
    if "host_received_ms" in diagnostic:
        diagnostic["host_snapshot_age_ms"] = (
            diagnostic["host_capture_ms"] - diagnostic["host_received_ms"]
        )
    diagnostic["counts"] = getattr(page, "_raceatlas_camera_counts", {})
    diagnostic["trace"] = list(diagnostic["trace"])
    while len(json.dumps(diagnostic)) > 12000 and diagnostic["trace"]:
        diagnostic["trace"].pop(0)
    return diagnostic


def launch(playwright, **kwargs):
    return playwright.chromium.launch(
        args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], **kwargs
    )
