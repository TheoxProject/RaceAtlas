"""Normalized business snapshots: no tokens, internal IDs, display noise or check times."""

import hashlib
import json
from dataclasses import asdict


def text(value):
    return " ".join(value.split()) if value is not None else None


def scope_facts(scope):
    rules = []
    for rule in scope.rules:
        restrictions = asdict(rule.restrictions)
        restrictions["engagers"] = sorted(text(item) for item in restrictions["engagers"])
        restrictions["other_text"] = text(restrictions["other_text"])
        rules.append({"categories": sorted(rule.category_codes), "restrictions": restrictions})
    # Ordering stays observable: changed unverified scopes are quarantined, never rematched.
    return {
        "kind": scope.kind,
        "eligibility": scope.eligibility_status,
        "rules": rules,
        # Labels detect ambiguity only; they are never a positive identity match.
        "raw_label": text(scope.raw_label),
    }


def observation_facts(observation):
    return {
        "name": text(observation.name),
        "discipline": observation.discipline,
        "types": sorted(observation.types),
        "organizer": text(observation.organizer),
        "start_date": observation.start_date.isoformat(),
        "end_date": observation.end_date.isoformat(),
        "department": observation.department,
        "status": observation.status,
        "scopes": [scope_facts(scope) for scope in observation.scopes],
    }


def fingerprint(facts):
    encoded = json.dumps(facts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
