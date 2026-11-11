import json
from copy import deepcopy
from pathlib import Path

import pytest
from werkzeug.datastructures import MultiDict

from raceatlas.catalog import CatalogError, parse_query
from raceatlas.catalog.cursor import decode_cursor, encode_cursor

ROOT = Path(__file__).resolve().parents[2]
FILTER = json.loads((ROOT / "fixtures/scenarios.v1.json").read_text(encoding="utf-8"))["scenarios"][
    0
]["filter"]


def query(value=None, **params):
    return parse_query(
        MultiDict({"filter": json.dumps(FILTER if value is None else value), **params})
    )


def test_canonical_equivalent_filters_and_neutral_category_operator_share_cursor_binding():
    first = deepcopy(FILTER)
    first.update(query=" ÉPREUVE  ", disciplines=["road", "gravel"], category_operator="and")
    second = deepcopy(first)
    second.update(query="e\u0301preuve", disciplines=["gravel", "road"], category_operator="or")
    a, b = query(first), query(second)
    assert a.filter_hash == b.filter_hash
    token = encode_cursor("epoch:1", a.filter_hash, 1)
    assert decode_cursor(token, "epoch:1", b.filter_hash) == 1


@pytest.mark.parametrize(
    "raw",
    [
        '{"from":"2026-01-01","from":"2027-01-01"}',
        '{"x": NaN}',
        '{"x":Infinity}',
        '{"x":1e999}',
        "[",
        "null",
        "[" * 1500 + "0" + "]" * 1500,
    ],
)
def test_invalid_json_duplicate_keys_and_nonfinite_values_are_public_errors(raw):
    with pytest.raises(CatalogError) as error:
        parse_query(MultiDict({"filter": raw}))
    assert error.value.status == 400
    assert error.value.code == "invalid_filter"


@pytest.mark.parametrize(
    "mutation",
    [
        {"from": "2026-02-30"},
        {"from": "2027-01-01", "to": "2026-01-01"},
        {"disciplines": ["clm"]},
        {"disciplines": ["gravel"], "types": ["time_trial"]},
        {"categories": ["open_1", "open_1"]},
        {"unexpected": True},
        {"geography": {"mode": "all", "departments": ["26"]}},
        {"geography": {"mode": "departments", "departments": ["75"]}},
        {"geography": {"mode": "radius", "center": [True, 45], "radius_km": 20}},
        {"geography": {"mode": "radius", "center": [4, 45], "radius_km": False}},
        {"geography": {"mode": "radius", "center": [181, 45], "radius_km": 20}},
        {"geography": {"mode": "radius", "center": [4, 45], "radius_km": 501}},
    ],
)
def test_contract_and_business_filter_validation_reject_invalid_forms(mutation):
    selected = deepcopy(FILTER)
    selected.update(mutation)
    with pytest.raises(CatalogError):
        query(selected)


@pytest.mark.parametrize(
    "args",
    [
        MultiDict(),
        MultiDict([("filter", "{}"), ("filter", "{}")]),
        MultiDict({"filter": "{}", "unknown": "x"}),
    ],
)
def test_missing_repeated_and_unknown_parameters_reject(args):
    with pytest.raises(CatalogError):
        parse_query(args)


@pytest.mark.parametrize("limit", ["", "0", "201", "1.0", "true", "-1", "9" * 100])
def test_limit_bounds_and_representation(limit):
    with pytest.raises(CatalogError) as error:
        query(limit=limit)
    assert error.value.fields == ["limit"]


def test_cursor_corruption_wrong_filter_and_stale_snapshot_are_distinct():
    parsed = query()
    token = encode_cursor("epoch:1", parsed.filter_hash, 1)
    for bad in ("not a token", token[:-1], token + "=", ""):
        with pytest.raises(CatalogError) as error:
            decode_cursor(bad, "epoch:1", parsed.filter_hash)
        assert error.value.status == 400
    with pytest.raises(CatalogError) as changed:
        decode_cursor(token, "epoch:2", parsed.filter_hash)
    assert changed.value.status == 409 and changed.value.code == "stale_cursor"
    with pytest.raises(CatalogError) as wrong_filter:
        decode_cursor(token, "epoch:1", "another-filter")
    assert wrong_filter.value.status == 400
