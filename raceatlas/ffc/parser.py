"""Strict offline parser; supported synthetic HTML dialect is documented in fixtures/ffc.

Known source selectors do not establish the complete live FFC HTML grammar. Unknown
layouts fail explicitly; this module neither fetches nor claims live compatibility.
"""

import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin, urlsplit, urlunsplit
from uuid import uuid4

from .html import Node, by_id, labeled_fields, read_html, single
from .types import (
    DEPARTMENTS,
    AdapterError,
    CalendarObservation,
    Diagnostic,
    RaceObservation,
    Restrictions,
    RuleObservation,
    ScopeObservation,
    SourceKey,
)

DISCIPLINES = {"route": "road", "gravel": "gravel", "vtt": "mtb", "cyclo-cross": "cyclocross"}
TYPES = {
    "course en ligne": ("road", "road_race"),
    "clm": ("road", "time_trial"),
    "gravel": ("gravel", "gravel_race"),
    "xco": ("mtb", "xco"),
    "enduro": ("mtb", "enduro"),
    "descente": ("mtb", "downhill"),
    "cyclo-cross": ("cyclocross", "cyclocross"),
}
CATEGORIES = {
    "elite": "elite",
    "élite": "elite",
    **{f"open {i}": f"open_{i}" for i in range(1, 4)},
    **{f"access {i}": f"access_{i}" for i in range(1, 5)},
    "u19": "u19",
    "u17": "u17",
}
SEX = {"hommes": "men", "femmes": "women", "tous": "any"}
STATUS = {"programmée": "scheduled", "annulée": "cancelled", "reportée": "postponed"}
RACE_PATH = re.compile(r"^/calendrier/competition/(\d{4})/([A-Za-z0-9_-]+)/([^/]*/)?$")


def _timestamp(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise AdapterError("invalid_timestamp", "checked_at", "Timezone-aware datetime required")
    return value


def _url(value, race=False):
    try:
        parts = urlsplit(value)
    except (ValueError, TypeError):
        raise AdapterError("invalid_source_url", "source_url", "Malformed source URL") from None
    if (
        parts.scheme != "https"
        or parts.netloc != "competitions.ffc.fr"
        or parts.username
        or parts.password
        or parts.fragment
    ):
        raise AdapterError("invalid_source_url", "source_url", "Expected public FFC HTTPS URL")
    if race:
        match = RACE_PATH.fullmatch(parts.path)
        if not match or parts.query:
            raise AdapterError(
                "invalid_source_key", "source_url", "Expected race season and number"
            )
        season = int(match[1])
        if not 2000 <= season <= 2200:
            raise AdapterError("invalid_source_key", "source_url", "Season outside supported range")
        return SourceKey(season, match[2])
    if parts.path != "/calendrier/":
        raise AdapterError("invalid_source_url", "source_url", "Expected calendar URL")


def _date(value, field):
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise AdapterError("invalid_date", field, "Expected a valid ISO civil date") from None


def _required(fields, key):
    if key not in fields:
        raise AdapterError("missing_field", key, "Required explicit source fact unavailable")
    return fields[key]


def _selection(root, name):
    node = single(
        root.all(lambda item: item.attrs.get("name") == name and item.tag in {"input", "select"}),
        name,
    )
    if node.tag == "input":
        return node.attrs.get("value", "")
    option = single(node.all(lambda item: item.tag == "option" and "selected" in item.attrs), name)
    return option.attrs.get("value", "")


def parse_calendar(html, *, source_url, checked_at, requested):
    _url(source_url)
    _timestamp(checked_at)
    if requested.department not in DEPARTMENTS:
        raise AdapterError("invalid_department", "requested", "Department outside AURA")
    if not isinstance(requested.start, date) or not isinstance(requested.end, date):
        raise AdapterError("invalid_window", "requested", "Civil dates required")
    if not 1 <= (requested.end - requested.start).days + 1 <= 14:
        raise AdapterError("invalid_window", "requested", "Requested duration must be 1–14 days")
    root = read_html(html)
    start = _date(_selection(root, "debut"), "effective_start")
    duration = _selection(root, "nbjours")
    if not re.fullmatch(r"[0-9]{1,2}", duration) or not 1 <= int(duration) <= 14:
        raise AdapterError("invalid_window", "nbjours", "Effective duration must be 1–14 days")
    end = start + timedelta(days=int(duration) - 1)
    department = _selection(root, "departement") or None
    if department is not None and department not in DEPARTMENTS:
        raise AdapterError("invalid_department", "effective_department", "Department outside AURA")
    counter = single(
        root.all(lambda item: item.attrs.get("id", "").endswith("InfoJourSelection")),
        "displayed_count",
    )
    match = re.fullmatch(r"(\d+) épreuves?", counter.text)
    if not match:
        raise AdapterError("layout_changed", "displayed_count", "Unrecognized source counter")
    keys = set()
    for link in root.all(lambda item: item.tag == "a"):
        href = link.attrs.get("href", "")
        try:
            absolute = urljoin(source_url, href)
            parts = urlsplit(absolute)
        except ValueError:
            raise AdapterError("invalid_source_url", "link", "Malformed calendar link") from None
        if "/calendrier/competition/" not in parts.path:
            continue
        # Ignore presentation slug; only the attested season/number form is identity.
        absolute = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        keys.add(_url(absolute, race=True))
    diagnostics = []
    if (start, end) != (requested.start, requested.end):
        diagnostics.append(Diagnostic("window_mismatch", "period", "Effective period differs"))
    if department != requested.department:
        diagnostics.append(
            Diagnostic("department_mismatch", "department", "Effective department differs")
        )
    count = int(match[1])
    if count != len(keys):
        diagnostics.append(
            Diagnostic("count_mismatch", "count", "Counter differs from distinct keys")
        )
    return CalendarObservation(
        source_url,
        checked_at,
        requested,
        start,
        end,
        department,
        count,
        tuple(sorted(keys, key=lambda key: (key.season, key.race_number))),
        "incomplete" if diagnostics else "consistent_sample",
        tuple(diagnostics),
    )


def _age(fields, key):
    value = fields.get(key)
    if value is None:
        return None
    if not re.fullmatch(r"\d{1,3}", value) or not 0 <= int(value) <= 120:
        raise AdapterError("invalid_restriction", key, "Invalid explicit age bound")
    return int(value)


def _rule(node):
    fields = labeled_fields(node)
    allowed = {
        "catégories",
        "sexe",
        "âge minimum",
        "âge maximum",
        "référence âge",
        "engageur",
        "autres restrictions",
    }
    raw = "; ".join(f"{key}: {value}" for key, value in fields.items())
    diagnostics = []
    labels = [item.strip() for item in re.split("[,;]", _required(fields, "catégories"))]
    categories = []
    for label in labels:
        code = CATEGORIES.get(label.casefold())
        if code is None:
            diagnostics.append(Diagnostic("unknown_category", "categories", "Unconfirmed label"))
        elif code not in categories:
            categories.append(code)
    if fields.keys() - allowed:
        diagnostics.append(Diagnostic("unknown_restriction", "rule", "Unrecognized criterion"))
    sex = SEX.get(fields.get("sexe", "").casefold(), "unknown")
    if "sexe" in fields and sex == "unknown":
        diagnostics.append(Diagnostic("unknown_restriction", "sex", "Unrecognized sex criterion"))
    min_age, max_age = _age(fields, "âge minimum"), _age(fields, "âge maximum")
    if min_age is not None and max_age is not None and min_age > max_age:
        raise AdapterError("invalid_restriction", "age", "Inverted age bounds")
    reference, season = "unknown", None
    age_label = fields.get("référence âge")
    if age_label:
        match = re.fullmatch(r"Fin de saison (\d{4})", age_label)
        if match and 2000 <= int(match[1]) <= 2200:
            reference, season = "season_end", int(match[1])
        elif age_label == "Date de l'épreuve":
            reference = "event_date"
        else:
            diagnostics.append(
                Diagnostic("unknown_restriction", "age_reference", "Unrecognized age reference")
            )
    if (min_age is not None or max_age is not None) and reference == "unknown":
        diagnostics.append(Diagnostic("unknown_restriction", "age", "Age reference unavailable"))
    engagers = tuple(
        dict.fromkeys(
            item.strip() for item in fields.get("engageur", "").split(";") if item.strip()
        )
    )
    restrictions = Restrictions(
        sex, min_age, max_age, reference, season, engagers, fields.get("autres restrictions")
    )
    # Partial or complex unknown rules cannot confirm even their recognized category subset.
    if diagnostics:
        return None, diagnostics
    return RuleObservation(str(uuid4()), tuple(categories), restrictions, raw, str(uuid4())), []


def parse_race(html, *, source_url, checked_at):
    key = _url(source_url, race=True)
    _timestamp(checked_at)
    root = read_html(html)
    canonical = root.all(lambda item: item.tag == "link" and item.attrs.get("rel") == "canonical")
    if canonical:
        link = single(canonical, "canonical")
        if _url(link.attrs.get("href", ""), race=True) != key:
            raise AdapterError("conflicting_source_key", "canonical", "Source identities disagree")
    fields = labeled_fields(by_id(root, "raceDetails"))
    allowed = {
        "nom",
        "discipline",
        "type sportif",
        "date de début",
        "date de fin",
        "département",
        "organisateur",
        "statut",
    }
    if fields.keys() - allowed:
        raise AdapterError("layout_changed", "raceDetails", "Unrecognized race fact label")
    discipline = DISCIPLINES.get(_required(fields, "discipline").casefold())
    if not discipline:
        raise AdapterError("unknown_discipline", "discipline", "Explicit discipline unsupported")
    department = _required(fields, "département")
    if department not in DEPARTMENTS:
        raise AdapterError("invalid_department", "department", "Department outside AURA")
    start = _date(_required(fields, "date de début"), "start_date")
    end = _date(_required(fields, "date de fin"), "end_date")
    if end < start:
        raise AdapterError("invalid_date", "end_date", "End date precedes start date")
    diagnostics, types = [], []
    for label in re.split("[,;]", fields.get("type sportif", "")):
        if not label.strip():
            continue
        item = TYPES.get(label.strip().casefold())
        if not item:
            diagnostics.append(Diagnostic("unknown_type", "types", "Unconfirmed sport type"))
        elif item[0] != discipline:
            raise AdapterError("incompatible_type", "types", "Sport type contradicts discipline")
        elif item[1] not in types:
            types.append(item[1])
    status = STATUS.get(fields.get("statut", "").casefold(), "unknown")
    if "statut" in fields and status == "unknown":
        diagnostics.append(Diagnostic("unknown_status", "status", "Unconfirmed source status"))
    container = by_id(root, "epreuvesContenu")
    lists = [
        child
        for child in container.children
        if isinstance(child, Node) and child.has_class("epreuve")
    ]
    if any(
        isinstance(child, Node) and not child.has_class("epreuve") for child in container.children
    ):
        raise AdapterError("layout_changed", "epreuvesContenu", "Unexpected source list container")
    scopes = []
    for entry in lists:
        if any(
            isinstance(child, Node)
            and not (child.tag == "h3" or child.tag == "dl" and child.has_class("regle"))
            for child in entry.children
        ):
            raise AdapterError("layout_changed", "scope", "Unrecognized eligibility structure")
        label = single(entry.all(lambda item: item.tag == "h3"), "scope_label").text
        if not label:
            raise AdapterError("missing_field", "scope_label", "Empty scope label")
        rule_nodes = entry.all(lambda item: item.tag == "dl" and item.has_class("regle"))
        rules, errors = [], []
        for node in rule_nodes:
            rule, found = _rule(node)
            errors.extend(found)
            if rule:
                rules.append(rule)
        diagnostics.extend(errors)
        if not rule_nodes:
            diagnostics.append(Diagnostic("unknown_eligibility", "scope", "No explicit rules"))
        # Preserve the exact selected rule facts even when normalization is ambiguous.
        raw_scope = "; ".join([label, *(node.text for node in rule_nodes)])
        scopes.append(
            ScopeObservation(
                str(uuid4()),
                "entry_list",
                raw_scope,
                "ambiguous" if errors else "confirmed" if rules else "unknown",
                tuple(rules),
            )
        )
    if not lists:
        diagnostics.append(
            Diagnostic("unknown_eligibility", "scope", "No source lists established")
        )
        # A placeholder race-level unknown scope is not an assertion of race-level eligibility.
        scopes.append(
            ScopeObservation(str(uuid4()), "race", "Admissibilité non établie", "unknown", ())
        )
    return RaceObservation(
        key,
        source_url,
        checked_at,
        _required(fields, "nom"),
        discipline,
        tuple(types),
        fields.get("organisateur"),
        start,
        end,
        department,
        status,
        tuple(scopes),
        tuple(diagnostics),
    )
