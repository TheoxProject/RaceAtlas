"""Explicit synthetic demonstration loader, not a provider import pipeline."""

import json
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select

from raceatlas.models import (
    Category,
    Commune,
    Competition,
    EligibilityRule,
    EntryScope,
    Race,
    RaceType,
    RuleCategory,
    SourceRecord,
)

CATALOG = Path(__file__).resolve().parents[1] / "fixtures" / "catalog.v1.json"


def seed_synthetic(session):
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["synthetic"] is True
    # Add-only demonstration seed: repeat runs never overwrite a developer's edits.
    for category in catalog["categories"]:
        if session.get(Category, category["code"]) is None:
            session.add(Category(**category))
    session.flush()
    added = 0
    for item in catalog["races"]:
        if session.get(Race, item["id"]) is not None:
            continue
        parent = item["competition_id"]
        if parent and session.get(Competition, parent) is None:
            session.add(
                Competition(
                    id=parent,
                    name="Manifestation synthétique",
                    grouping_evidence="fixtures/catalog.v1.json",
                )
            )
            session.flush()
        location = item["location"]
        if location and session.get(Commune, location["commune_id"]) is None:
            coordinates = location["coordinates"]
            session.add(
                Commune(
                    id=location["commune_id"],
                    insee_code=location["insee_code"],
                    name=location["commune_name"],
                    department=location["department"],
                    longitude=coordinates[0] if coordinates else None,
                    latitude=coordinates[1] if coordinates else None,
                    precision=location["precision"],
                    provenance=location["provenance"],
                    geocoded_at=(
                        datetime.fromisoformat(location["geocoded_at"])
                        if location["geocoded_at"]
                        else None
                    ),
                )
            )
            session.flush()
        fields = {
            key: item[key]
            for key in (
                "id",
                "competition_id",
                "name",
                "discipline",
                "organizer",
                "department",
                "status",
                "source_presence",
                "revision",
            )
        }
        race = Race(
            **fields,
            commune_id=location["commune_id"] if location else None,
            start_date=date.fromisoformat(item["start_date"]),
            end_date=date.fromisoformat(item["end_date"]),
        )
        race.types = [RaceType(code=code) for code in item["types"]]
        source = item["source"].copy()
        source["checked_at"] = datetime.fromisoformat(source["checked_at"])
        race.source = SourceRecord(**source)
        for position, entry in enumerate(item["entry_scopes"]):
            scope = EntryScope(
                **{
                    key: entry[key]
                    for key in (
                        "id",
                        "kind",
                        "source_list_id",
                        "identity_status",
                        "eligibility_status",
                        "raw_label",
                    )
                },
                position=position,
            )
            for index, definition in enumerate(entry["rules"]):
                rule = EligibilityRule(
                    id=definition["id"],
                    position=index,
                    raw_label=definition["raw_label"],
                    evidence_id=definition["evidence_id"],
                    **definition["restrictions"],
                )
                rule.categories = [
                    RuleCategory(category_code=code, position=i)
                    for i, code in enumerate(definition["category_codes"])
                ]
                scope.rules.append(rule)
            race.scopes.append(scope)
        session.add(race)
        session.flush()
        added += 1
    return added


def demo_id(session):
    return session.scalar(
        select(Race.id)
        .join(SourceRecord)
        .where(SourceRecord.provider == "synthetic")
        .order_by(Race.id)
        .limit(1)
    )
