"""Pure reader for the FFC public calendar and race detail HTML.

Reconciled calendar metadata describes the displayed sample. It does not
establish source coverage or justify marking previously seen races missing.
"""

import re
from datetime import date, timedelta
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

from .html import Node, Reader, by_id, read_html, single
from .parser import DISCIPLINES, STATUS, TYPES, _timestamp, _url
from .types import (
    DEPARTMENTS,
    AdapterError,
    CalendarObservation,
    Diagnostic,
    RaceObservation,
    Restrictions,
    RuleObservation,
    ScopeObservation,
)

DEPARTMENT_NAMES = {
    "ain": "01",
    "allier": "03",
    "ardèche": "07",
    "cantal": "15",
    "drôme": "26",
    "isère": "38",
    "loire": "42",
    "haute-loire": "43",
    "puy-de-dôme": "63",
    "rhône": "69",
    "savoie": "73",
    "haute-savoie": "74",
}
MONTHS = (
    "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
)
WEEKDAYS = "lundi mardi mercredi jeudi vendredi samedi dimanche".split()
COUNT = re.compile(r"([0-9]{1,6}) compétitions? du (.+) au (.+)")
SINGLE_DAY_COUNT = re.compile(r"([0-9]{1,6}) compétitions? le (.+)")
DETAIL_PREFIX = "/calendrier/competition/"
CRITERIA = "critères d'admissibilité"
ENGAGERS = "Engagements réservés pour :"
RANGES = {
    "de u17 à u17": ("u17",),
    "de u19 à u19": ("u19",),
    "de access 1 à access 4": ("access_1", "access_2", "access_3", "access_4"),
    "de open 1 à open 3": ("open_1", "open_2", "open_3"),
}
SEXES = {"hommes tout âge": "men", "femmes tout âge": "women"}


class _DetailReader(Reader):
    def handle_endtag(self, tag):
        if (
            tag == "span"
            and len(self.stack) >= 3
            and self.stack[-2].tag == "span"
            and self.stack[-1].tag == "div"
            and self.stack[-1].attrs.get("id") == "organisationView"
        ):
            # The public detail template omits the organisation wrapper's end tag.
            self.stack.pop()
        super().handle_endtag(tag)


def _read_detail(html):
    if not isinstance(html, str) or len(html) > 2_000_000:
        raise AdapterError("html_limit", "html", "Expected bounded HTML text")
    parser = _DetailReader()
    parser.feed(html)
    parser.close()
    if len(parser.stack) != 1:
        raise AdapterError("html_structure", "html", "Unclosed document elements")
    return parser.root


def _civil_day(value, field):
    match = re.fullmatch(r"([a-z]+) ([0-9]{1,2}) (\S+) ([0-9]{4})", value.casefold())
    if match is None:
        raise AdapterError("invalid_date", field, "Expected an explicit FFC civil date")
    weekday, day, month, year = match.groups()
    try:
        result = date(int(year), MONTHS.index(month) + 1, int(day))
    except ValueError:
        raise AdapterError("invalid_date", field, "Invalid FFC civil date") from None
    if WEEKDAYS[result.weekday()] != weekday:
        raise AdapterError("invalid_date", field, "Weekday contradicts civil date")
    return result


def _race_dates(raw_date, raw_duration):
    duration = re.fullmatch(r"([0-9]{1,2}) jours?", raw_duration.casefold())
    if duration is None or not 1 <= int(duration[1]) <= 31:
        raise AdapterError("invalid_date", "duration", "Expected an explicit race duration")
    days = int(duration[1])
    period = re.fullmatch(r"du (.+) au (.+)", raw_date.casefold())
    if period:
        start = _civil_day(period[1], "start_date")
        end = _civil_day(period[2], "end_date")
        if (end - start).days + 1 != days:
            raise AdapterError("invalid_date", "duration", "Date range contradicts race duration")
        return start, end
    start = _civil_day(raw_date, "start_date")
    try:
        return start, start + timedelta(days=days - 1)
    except OverflowError:
        raise AdapterError(
            "invalid_date", "duration", "Race duration exceeds civil dates"
        ) from None


def _selected(root, identifier):
    select = by_id(root, identifier)
    if select.tag != "select":
        raise AdapterError("layout_changed", identifier, "Expected a calendar selection")
    option = single(
        select.all(lambda node: node.tag == "option" and "selected" in node.attrs), identifier
    )
    return option.attrs.get("value", "")


def _calendar_dates(root):
    counter = single(
        root.all(lambda node: node.attrs.get("id", "").endswith("InfoJourSelection")),
        "displayed_count",
    ).text.casefold()
    period = COUNT.fullmatch(counter)
    if period:
        count, start, end = period.groups()
        return int(count), _civil_day(start, "effective_start"), _civil_day(end, "effective_end")
    day = SINGLE_DAY_COUNT.fullmatch(counter)
    if day:
        start = _civil_day(day[2], "effective_start")
        return int(day[1]), start, start
    raise AdapterError("layout_changed", "displayed_count", "Unrecognized public counter")


def parse_public_calendar(html, *, source_url, checked_at, requested):
    """Return the observed calendar window and its verified public detail links."""
    _url(source_url)
    _timestamp(checked_at)
    if requested.department not in DEPARTMENTS:
        raise AdapterError("invalid_department", "requested", "Department outside AURA")
    if type(requested.start) is not date or type(requested.end) is not date:
        raise AdapterError("invalid_window", "requested", "Civil dates required")
    if not 1 <= (requested.end - requested.start).days + 1 <= 14:
        raise AdapterError("invalid_window", "requested", "Requested duration must be 1–14 days")

    root = read_html(html)
    count, start, end = _calendar_dates(root)
    department = _selected(root, "filtreDepartementID") or None
    if department is not None and department not in DEPARTMENTS:
        raise AdapterError("invalid_department", "effective_department", "Department outside AURA")
    duration = _selected(root, "filtreNombreDeJoursID")
    if re.fullmatch(r"[0-9]{1,2}", duration) is None or not 1 <= int(duration) <= 14:
        raise AdapterError("invalid_window", "duration", "Effective duration must be 1–14 days")

    links = {}
    for anchor in root.all(lambda node: node.tag == "a"):
        href = anchor.attrs.get("href", "")
        try:
            detail_url = urljoin(source_url, href)
            parts = urlsplit(detail_url)
        except ValueError:
            raise AdapterError("invalid_source_url", "link", "Malformed calendar link") from None
        if not parts.path.startswith(DETAIL_PREFIX):
            continue
        key = _url(detail_url, race=True)
        links.setdefault(key, detail_url)

    diagnostics = []
    if (start, end) != (requested.start, requested.end) or (end - start).days + 1 != int(duration):
        diagnostics.append(Diagnostic("window_mismatch", "period", "Effective period differs"))
    if department != requested.department:
        diagnostics.append(
            Diagnostic("department_mismatch", "department", "Effective department differs")
        )
    if count != len(links):
        diagnostics.append(
            Diagnostic("count_mismatch", "count", "Counter differs from distinct keys")
        )
    keys = tuple(sorted(links, key=lambda key: (key.season, key.race_number)))
    return (
        CalendarObservation(
            source_url,
            checked_at,
            requested,
            start,
            end,
            department,
            count,
            keys,
            "incomplete" if diagnostics else "consistent_sample",
            tuple(diagnostics),
        ),
        {key: links[key] for key in keys},
    )


def _class_text(root, name):
    return single(root.all(lambda node: node.has_class(name)), name).text


def _race_fields(view):
    fields = {}
    info = by_id(view, "infosPrincipales")
    for item in info.all(lambda node: node.has_class("info-principale")):
        label = _class_text(item, "titreValeur-titre").casefold()
        if not label or label in fields:
            raise AdapterError("duplicate_field", "race", "Missing or repeated race field label")
        fields[label] = _class_text(item, "titreValeur-valeur")
    return fields


def _is_criteria_title(node):
    return node.has_class("epreuve-titre") and node.text.casefold().replace("’", "'") == CRITERIA


def _known_criteria_layout(description, found_badges):
    sections = description.all(
        lambda node: any(
            isinstance(child, Node) and _is_criteria_title(child) for child in node.children
        )
    )
    if len(sections) != 1:
        return False
    items = [child for child in sections[0].children if isinstance(child, Node) or child.strip()]
    if (
        len(items) != 2
        or not all(isinstance(item, Node) for item in items)
        or not _is_criteria_title(items[0])
        or not items[1].has_class("horizontal")
    ):
        return False
    badges = [child for child in items[1].children if isinstance(child, Node) or child.strip()]
    return (
        bool(badges)
        and all(isinstance(badge, Node) and badge.has_class("epreuve-badge") for badge in badges)
        and [badge.text for badge in badges] == list(found_badges)
    )


def _scope(entry):
    descriptions = entry.all(lambda node: node.has_class("epreuve-description"))
    if len(descriptions) != 1:
        return ScopeObservation(
            str(uuid4()), "entry_list", "Admissibilité non établie", "unknown", ()
        )
    description = descriptions[0]
    raw_badges = tuple(
        node.text for node in description.all(lambda node: node.has_class("epreuve-badge"))
    )
    engager_texts = tuple(
        node.text
        for node in description.all(
            lambda node: node.tag == "div"
            and not any(isinstance(child, Node) for child in node.children)
        )
        if node.text.startswith(ENGAGERS)
    )
    raw = "; ".join((*raw_badges, *engager_texts))
    normalized = tuple(label.casefold() for label in raw_badges)
    categories = [RANGES[label] for label in normalized if label in RANGES]
    sexes = [SEXES[label] for label in normalized if label in SEXES]
    if (
        not _known_criteria_layout(description, raw_badges)
        or len(categories) != 1
        or not sexes
        or len(set(sexes)) != len(sexes)
        or len(categories) + len(sexes) != len(normalized)
        or len(engager_texts) > 1
    ):
        return ScopeObservation(
            str(uuid4()), "entry_list", raw or "Admissibilité non établie", "unknown", ()
        )
    engagers = ()
    if engager_texts:
        engagers = tuple(
            value.strip()
            for value in engager_texts[0].removeprefix(ENGAGERS).split(",")
            if value.strip()
        )
        if not engagers:
            return ScopeObservation(str(uuid4()), "entry_list", raw, "unknown", ())
    rules = tuple(
        RuleObservation(
            str(uuid4()),
            categories[0],
            Restrictions(sex, None, None, "unknown", None, engagers, None),
            raw,
            str(uuid4()),
        )
        for sex in sexes
    )
    return ScopeObservation(str(uuid4()), "entry_list", raw, "confirmed", rules)


def parse_public_race(html, *, source_url, checked_at, expected_key, expected_department):
    """Return attested race facts and an explicit commune when available."""
    key = _url(source_url, race=True)
    _timestamp(checked_at)
    if key != expected_key:
        raise AdapterError("conflicting_source_key", "source_url", "Calendar and detail differ")
    if expected_department not in DEPARTMENTS:
        raise AdapterError("invalid_department", "expected", "Department outside AURA")

    root = _read_detail(html)
    view = by_id(root, "organisationView")
    title = by_id(view, "OrganisationTitleID")
    discipline = DISCIPLINES.get(_class_text(title, "discipline").casefold())
    if discipline is None:
        raise AdapterError(
            "unsupported_discipline", "discipline", "Discipline outside RaceAtlas V1"
        )
    name = single(title.all(lambda node: node.tag == "h1"), "race_name").text
    if not name:
        raise AdapterError("missing_field", "race_name", "Expected an explicit race name")

    fields = _race_fields(view)
    if fields.get("n° d'épreuve") != key.race_number or fields.get("saison") != str(key.season):
        raise AdapterError(
            "conflicting_source_key", "race", "URL and explicit race identity differ"
        )
    start, end = _race_dates(_class_text(title, "date"), fields.get("durée", ""))

    localisations = title.all(lambda node: node.has_class("localisation"))
    if localisations:
        location = single(localisations, "department").text.casefold()
        if location and DEPARTMENT_NAMES.get(location) != expected_department:
            raise AdapterError(
                "department_mismatch", "race", "Calendar and detail department differ"
            )

    type_fact = TYPES.get(fields.get("type sportif", "").casefold())
    if type_fact and type_fact[0] != discipline:
        raise AdapterError("incompatible_type", "types", "Sport type contradicts discipline")
    diagnostics = []
    if "type sportif" in fields and not type_fact:
        diagnostics.append(Diagnostic("unknown_type", "types", "Unconfirmed sport type"))
    status = STATUS.get(fields.get("statut", "").casefold(), "unknown")
    if "statut" in fields and status == "unknown":
        diagnostics.append(Diagnostic("unknown_status", "status", "Unconfirmed source status"))

    scope_containers = view.all(lambda node: node.attrs.get("id") == "epreuvesContenu")
    scopes = ()
    if scope_containers:
        container = single(scope_containers, "epreuvesContenu")
        scopes = tuple(
            _scope(node)
            for node in container.children
            if isinstance(node, Node) and node.has_class("epreuve")
        )
    if not scopes:
        scopes = (
            ScopeObservation(str(uuid4()), "race", "Admissibilité non établie", "unknown", ()),
        )
    if any(scope.eligibility_status == "unknown" for scope in scopes):
        diagnostics.append(
            Diagnostic("unknown_eligibility", "scope", "Unconfirmed public criteria")
        )

    return (
        RaceObservation(
            key,
            source_url,
            checked_at,
            name,
            discipline,
            (type_fact[1],) if type_fact else (),
            fields.get("organisateur") or None,
            start,
            end,
            expected_department,
            status,
            scopes,
            tuple(diagnostics),
        ),
        fields.get("commune") or None,
    )
