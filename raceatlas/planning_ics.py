"""Pure all-day ICS codec. No ORM, timezone assumptions, transport or parser dependency."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

from raceatlas.planning_snapshot import PlanningLimitError

UID_NAMESPACE = uuid5(
    NAMESPACE_URL, "https://github.com/TheoxProject/RaceAtlas/private-calendar/v1"
)
PRODID = "-//RaceAtlas//Private planning V1//FR"


@dataclass(frozen=True)
class EventPayload:
    scope_id: str
    saved_entry_id: str
    properties: tuple[tuple[str, str], ...]

    @property
    def fingerprint(self):
        content = json.dumps(
            [self.saved_entry_id, self.properties], ensure_ascii=False, separators=(",", ":")
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EventMetadata:
    stamp: datetime
    sequence: int


def event_uid(account_id, scope_id):
    name = json.dumps(["v1", account_id, scope_id], ensure_ascii=False, separators=(",", ":"))
    return str(uuid5(UID_NAMESPACE, name))


def _text(value, limits):
    if not isinstance(value, str):
        raise PlanningLimitError()
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        raise PlanningLimitError() from None
    if size > limits.text_bytes or any(
        ord(c) < 32 and c not in "\t\r\n" or ord(c) == 127 for c in value
    ):
        raise PlanningLimitError()
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _day(value):
    try:
        result = date.fromisoformat(value)
        if result.isoformat() != value:
            raise ValueError()
        return result
    except (ValueError, TypeError):
        raise PlanningLimitError() from None


def _date_value(value):
    return f"{value.year:04d}{value.month:02d}{value.day:02d}"


def event_payloads(items, account_id, limits):
    selected = [item for item in items if item["status"] in ("planned", "registered")]
    if len(selected) > limits.events:
        raise PlanningLimitError()
    result = []
    for item in sorted(
        selected, key=lambda x: (x["race"]["start_date"], x["race"]["end_date"], x["scope_id"])
    ):
        race, scope = item["race"], item["scope"]
        start, end = _day(race["start_date"]), _day(race["end_date"])
        try:
            exclusive = end + timedelta(days=1)
        except OverflowError:
            raise PlanningLimitError() from None
        if end < start:
            raise PlanningLimitError()
        source = race["source"]
        lines = [
            "Statut personnel : "
            + (
                "Planifié"
                if item["status"] == "planned"
                else "Inscrit (déclaré par vous, non vérifié par la FFC)"
            ),
            "Discipline : " + race["discipline"],
            "Types : " + ", ".join(sorted(race["types"])),
            "État source : " + race["status"],
            "Présence source : " + race["source_presence"],
            "Admissibilité personnelle non évaluée ; vérifier les restrictions de cette liste.",
            "Identité liste : "
            + scope["identity_status"]
            + "; admissibilité source : "
            + scope["eligibility_status"],
        ]
        rules = sorted(
            scope["rules"],
            key=lambda rule: json.dumps(
                [rule["raw_label"], sorted(rule["category_codes"]), rule["restrictions"]],
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
        for rule in rules:
            restrictions = json.dumps(
                rule["restrictions"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            lines.append(
                "Règle : "
                + rule["raw_label"]
                + " | catégories : "
                + ", ".join(sorted(rule["category_codes"]))
                + " | restrictions : "
                + restrictions
            )
        lines.append(
            f"Provenance : {source['provider']} / {source['source_season']} / "
            f"{source['race_number']} / {source['source_url']}"
        )
        location = race["location"]
        location_text = (
            "Lieu non localisé ; départ inconnu."
            if location is None
            else f"{location['commune_name']} ({location['department']}) ; "
            "centre de commune, départ inconnu."
        )
        properties = [
            ("UID", event_uid(account_id, scope["id"])),
            ("DTSTART;VALUE=DATE", _date_value(start)),
            ("DTEND;VALUE=DATE", _date_value(exclusive)),
            ("SUMMARY", _text(race["name"] + " — " + scope["raw_label"], limits)),
            ("DESCRIPTION", _text("\n".join(lines), limits)),
            ("LOCATION", _text(location_text, limits)),
        ]
        if race["status"] == "cancelled":
            properties.append(("STATUS", "CANCELLED"))
        result.append(EventPayload(scope["id"], item["id"], tuple(properties)))
    return result


def fold_line(line):
    """75 UTF-8 octets INCLUDING the continuation space, never split a codepoint."""
    current = bytearray()
    output = []
    for character in line:
        encoded = character.encode("utf-8")
        if len(current) + len(encoded) > 75:
            output.append(bytes(current))
            current = bytearray(b" ")
        current.extend(encoded)
    output.append(bytes(current))
    return b"\r\n".join(output) + b"\r\n"


def render_calendar(payloads, metadata, limits):
    output = bytearray()

    def emit(line):
        output.extend(fold_line(line))
        if len(output) > limits.response_bytes:
            raise PlanningLimitError()

    emit("BEGIN:VCALENDAR")
    emit("VERSION:2.0")
    emit("PRODID:" + PRODID)
    for payload in payloads:
        state = metadata[payload.scope_id]
        stamp = state.stamp
        if stamp.tzinfo is None or not 0 <= state.sequence <= 2147483647:
            raise PlanningLimitError()
        stamp = stamp.astimezone(timezone.utc)
        emit("BEGIN:VEVENT")
        for name, value in payload.properties:
            emit(name + ":" + value)
        emit(
            "DTSTAMP:"
            + _date_value(stamp.date())
            + f"T{stamp.hour:02d}{stamp.minute:02d}{stamp.second:02d}Z"
        )
        emit("SEQUENCE:" + str(state.sequence))
        emit("END:VEVENT")
    emit("END:VCALENDAR")
    return bytes(output)
