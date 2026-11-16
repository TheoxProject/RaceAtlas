"""Detached immutable notification facts, not source identity reconciliation."""

import json
from dataclasses import dataclass

from raceatlas.changes import ChangeError, canonical
from raceatlas.serialization import race_document

from .fingerprint import text


@dataclass(frozen=True)
class ChangeFacts:
    scopes: tuple[tuple[str, bytes], ...]
    presence: str


def snapshot(race):
    document = race_document(race)
    location = document["location"]
    common = {
        key: document[key]
        for key in ("name", "start_date", "end_date", "status", "discipline", "organizer")
    }
    common["name"], common["organizer"] = text(common["name"]), text(common["organizer"])
    common["types"] = sorted(set(document["types"]))
    common["competition"] = document["competition_id"]
    # A commune's identity is a fact; its centre/cache timestamp is not a race change.
    common["commune"] = {
        "department": document["department"],
        "insee_code": location["insee_code"] if location else None,
        "name": text(location["commune_name"]) if location else None,
    }
    scopes = []
    for scope in document["entry_scopes"]:
        rules = {}
        for rule in scope["rules"]:
            restrictions = dict(rule["restrictions"])
            restrictions["engagers"] = sorted({text(value) for value in restrictions["engagers"]})
            restrictions["other_text"] = text(restrictions["other_text"])
            normalized = {
                "categories": sorted(set(rule["category_codes"])),
                "restrictions": restrictions,
                "raw_label": text(rule["raw_label"]),
            }
            rules[canonical(normalized)] = normalized
        facts = {
            **common,
            "raw_label": text(scope["raw_label"]),
            "eligibility": {
                "kind": scope["kind"],
                "identity_status": scope["identity_status"],
                "status": scope["eligibility_status"],
                "rules": [rules[key] for key in sorted(rules)],
            },
        }
        scopes.append((scope["id"], canonical(facts)))
    return ChangeFacts(tuple(sorted(scopes)), document["source_presence"])


def deltas(before, after):
    old, new = dict(before.scopes), dict(after.scopes)
    if set(old) != set(new):
        raise ChangeError("Notification scope identity changed")
    return {
        scope_id: {"before": json.loads(old[scope_id]), "after": json.loads(new[scope_id])}
        for scope_id in old
        if old[scope_id] != new[scope_id]
    }
