"""Contract-driven, bounded validation of public catalogue query parameters."""

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts/catalog.schema.json").read_text(
        encoding="utf-8"
    )
)
FILTER_VALIDATOR = Draft202012Validator(
    {"$defs": SCHEMA["$defs"], "$ref": "#/$defs/Filter"}, format_checker=FormatChecker()
)
TYPE_DISCIPLINE = {
    "road_race": "road",
    "time_trial": "road",
    "gravel_race": "gravel",
    "xco": "mtb",
    "enduro": "mtb",
    "downhill": "mtb",
    "cyclocross": "cyclocross",
}


class CatalogError(ValueError):
    def __init__(self, code="invalid_filter", *, fields=(), status=400):
        self.code, self.fields, self.status = code, list(fields), status
        super().__init__(code)


def normalize(value):
    decomposed = unicodedata.normalize("NFD", value)
    return " ".join(re.sub(r"[\u0300-\u036f]", "", decomposed).lower().split())


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def _bounded(value, depth=0):
    if depth > 20 or isinstance(value, float) and not math.isfinite(value):
        raise ValueError("invalid_structure")
    if isinstance(value, dict):
        for item in value.values():
            _bounded(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _bounded(item, depth + 1)


def parse_json(value, *, max_length=16384):
    if not isinstance(value, str) or len(value) > max_length:
        raise ValueError("invalid_json")
    result = json.loads(value, object_pairs_hook=_pairs)
    _bounded(result)
    return result


@dataclass(frozen=True)
class Query:
    filter: dict
    filter_hash: str
    start: date
    end: date
    limit: int
    cursor: str | None


def parse_query(args):
    invalid = sorted(
        key
        for key in args
        if key not in {"filter", "limit", "cursor"} or len(args.getlist(key)) != 1
    )
    if invalid:
        raise CatalogError(fields=invalid)
    if "filter" not in args:
        raise CatalogError(fields=["filter"])
    try:
        selected = parse_json(args["filter"])
    except (ValueError, TypeError, RecursionError):
        raise CatalogError(fields=["filter"]) from None
    errors = list(FILTER_VALIDATOR.iter_errors(selected))
    if errors:
        fields = sorted(
            {"filter" + "".join(f".{part}" for part in error.absolute_path) for error in errors}
        )
        raise CatalogError(fields=fields)
    start, end = date.fromisoformat(selected["from"]), date.fromisoformat(selected["to"])
    if start > end:
        raise CatalogError(fields=["filter.from", "filter.to"])
    if selected["disciplines"] and any(
        TYPE_DISCIPLINE[item] not in selected["disciplines"] for item in selected["types"]
    ):
        raise CatalogError(fields=["filter.types"])
    raw_limit = args.get("limit", "100")
    if not re.fullmatch(r"[0-9]{1,3}", raw_limit) or not 1 <= int(raw_limit) <= 200:
        raise CatalogError(fields=["limit"])
    cursor = args.get("cursor")
    if cursor is not None and (not cursor or len(cursor) > 4096):
        raise CatalogError(fields=["cursor"])
    for key in ("disciplines", "types", "categories"):
        selected[key] = sorted(selected[key])
    selected["query"] = normalize(selected["query"])
    if not selected["categories"]:
        selected["category_operator"] = "or"
    if selected["geography"]["mode"] == "departments":
        selected["geography"]["departments"].sort()
    if selected["geography"]["mode"] == "radius":
        geography = selected["geography"]
        geography["center"] = [float(value) for value in geography["center"]]
        geography["radius_km"] = float(geography["radius_km"])
    encoded = json.dumps(selected, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return Query(
        selected,
        hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        start,
        end,
        int(raw_limit),
        cursor,
    )
