"""Deterministic synthetic map resources; real MapLibre/Chromium WebGL remains active."""

import json
import math
import struct
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


def launch(playwright, **kwargs):
    return playwright.chromium.launch(
        args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], **kwargs
    )
