from datetime import timezone


def timestamp(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if value else None


def race_document(race):
    commune = race.commune
    location = None
    if commune:
        location = {
            "commune_id": commune.id,
            "insee_code": commune.insee_code,
            "commune_name": commune.name,
            "department": commune.department,
            "coordinates": (
                [commune.longitude, commune.latitude] if commune.longitude is not None else None
            ),
            "precision": commune.precision,
            "provenance": commune.provenance,
            "geocoded_at": timestamp(commune.geocoded_at),
        }
    return {
        "id": race.id,
        "competition_id": race.competition_id,
        "name": race.name,
        "discipline": race.discipline,
        "types": [item.code for item in race.types],
        "organizer": race.organizer,
        "start_date": race.start_date.isoformat(),
        "end_date": race.end_date.isoformat(),
        "status": race.status,
        "source_presence": race.source_presence,
        "location": location,
        "department": race.department,
        "revision": race.revision,
        "personal_eligibility": "not_evaluated",
        "source": {
            "provider": race.source.provider,
            "source_season": race.source.source_season,
            "race_number": race.source.race_number,
            "source_url": race.source.source_url,
            "checked_at": timestamp(race.source.checked_at),
        },
        "entry_scopes": [
            {
                "id": scope.id,
                "kind": scope.kind,
                "source_list_id": scope.source_list_id,
                "identity_status": scope.identity_status,
                "eligibility_status": scope.eligibility_status,
                "raw_label": scope.raw_label,
                "rules": [
                    {
                        "id": rule.id,
                        "category_codes": [item.category_code for item in rule.categories],
                        "restrictions": {
                            key: getattr(rule, key)
                            for key in (
                                "sex",
                                "min_age",
                                "max_age",
                                "age_reference",
                                "age_season",
                                "engagers",
                                "other_text",
                            )
                        },
                        "raw_label": rule.raw_label,
                        "evidence_id": rule.evidence_id,
                    }
                    for rule in scope.rules
                ],
            }
            for scope in race.scopes
        ],
    }
