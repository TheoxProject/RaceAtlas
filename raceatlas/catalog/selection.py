"""One PostgreSQL selector for catalogue and map, in a single read-only MVCC snapshot."""

from sqlalchemy import and_, distinct, exists, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from raceatlas.models import (
    CatalogState,
    Category,
    Commune,
    EligibilityRule,
    EntryScope,
    Race,
    RaceType,
    RuleCategory,
)
from raceatlas.serialization import race_document

from .coverage import coverage_document
from .cursor import decode_cursor, encode_cursor
from .validation import CatalogError


def _witnesses(race, selected):
    if not selected["categories"]:
        return [scope.id for scope in race.scopes]
    wanted = set(selected["categories"])
    result = []
    for scope in race.scopes:
        if scope.eligibility_status != "confirmed":
            continue
        accepted = {item.category_code for rule in scope.rules for item in rule.categories}
        if (
            wanted <= accepted
            if selected["category_operator"] == "and"
            else bool(wanted & accepted)
        ):
            result.append(scope.id)
    return result


def _base(query):
    selected = query.filter
    scopes = select(EntryScope.id).where(EntryScope.race_id == Race.id)
    if selected["categories"]:
        accepted = (
            select(EligibilityRule.scope_id)
            .join(RuleCategory)
            .where(RuleCategory.category_code.in_(selected["categories"]))
            .group_by(EligibilityRule.scope_id)
        )
        if selected["category_operator"] == "and":
            accepted = accepted.having(
                func.count(distinct(RuleCategory.category_code)) == len(selected["categories"])
            )
        scopes = scopes.where(
            EntryScope.eligibility_status == "confirmed", EntryScope.id.in_(accepted)
        )
    statement = (
        select(Race.id, Race.start_date)
        .outerjoin(Commune, Race.commune_id == Commune.id)
        .where(
            Race.start_date <= query.end,
            Race.end_date >= query.start,
            exists(scopes),
            Race.department.in_(
                ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"]
            ),
        )
    )
    if selected["disciplines"]:
        statement = statement.where(Race.discipline.in_(selected["disciplines"]))
    if selected["types"]:
        statement = statement.where(
            exists(
                select(RaceType.race_id).where(
                    RaceType.race_id == Race.id, RaceType.code.in_(selected["types"])
                )
            )
        )
    if selected["query"]:
        searchable = func.catalog_normalize(
            func.concat(
                Race.name,
                " ",
                func.coalesce(Commune.name, ""),
                " ",
                func.coalesce(Race.organizer, ""),
            )
        )
        statement = statement.where(searchable.contains(selected["query"], autoescape=True))
    geography = selected["geography"]
    if geography["mode"] == "departments":
        statement = statement.where(Race.department.in_(geography["departments"]))
    return statement


def _distance(center):
    longitude, latitude = center
    h = func.pow(func.sin(func.radians(Commune.latitude - latitude) / 2), 2) + (
        func.cos(func.radians(latitude))
        * func.cos(func.radians(Commune.latitude))
        * func.pow(func.sin(func.radians(Commune.longitude - longitude) / 2), 2)
    )
    return 2 * 6371.0088 * func.asin(func.sqrt(func.least(1.0, func.greatest(0.0, h))))


def _read(session, query, *, map_projection):
    state = session.get(CatalogState, 1)
    if state is None:
        raise CatalogError("unavailable", status=503)
    version = f"{state.epoch}:{state.revision}"
    offset = decode_cursor(query.cursor, version, query.filter_hash)
    selected = query.filter
    if selected["categories"]:
        known = set(
            session.scalars(select(Category.code).where(Category.code.in_(selected["categories"])))
        )
        if known != set(selected["categories"]):
            raise CatalogError(fields=["filter.categories"])
    base = _base(query)
    has_center = and_(
        Commune.longitude.is_not(None),
        Commune.latitude.is_not(None),
        Commune.precision == "commune_center",
    )
    unlocated = base.where(~has_center)
    radius = selected["geography"]["mode"] == "radius"
    matched = (
        base.where(
            has_center,
            _distance(selected["geography"]["center"]) <= selected["geography"]["radius_km"],
        )
        if radius
        else base
    )
    total = session.scalar(select(func.count()).select_from(matched.subquery()))
    unlocated_count = session.scalar(select(func.count()).select_from(unlocated.subquery()))
    universe = max(total, unlocated_count) if radius else total
    if query.cursor is not None and offset >= universe:
        raise CatalogError(fields=["cursor"])
    ids = list(
        session.scalars(
            matched.order_by(Race.start_date, Race.id.collate("C"))
            .offset(offset)
            .limit(query.limit)
        )
    )
    races = (
        session.scalars(
            select(Race)
            .where(Race.id.in_(ids))
            .options(
                joinedload(Race.source),
                joinedload(Race.commune),
                selectinload(Race.types),
                selectinload(Race.scopes)
                .selectinload(EntryScope.rules)
                .selectinload(EligibilityRule.categories),
            )
        ).all()
        if ids
        else []
    )
    by_id = {race.id: race for race in races}
    items, features, unlocated_ids = [], [], []
    for race_id in ids:
        race = by_id[race_id]
        witnesses = _witnesses(race, selected)
        if not map_projection:
            items.append({"race": race_document(race), "matching_scope_ids": witnesses})
        commune = race.commune
        if commune is not None and commune.longitude is not None and commune.latitude is not None:
            features.append(
                {
                    "type": "Feature",
                    "id": race.id,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [commune.longitude, commune.latitude],
                    },
                    "properties": {
                        "race_id": race.id,
                        "commune_id": commune.id,
                        "discipline": race.discipline,
                        "matching_scope_ids": witnesses,
                    },
                }
            )
        elif not radius:
            unlocated_ids.append(race.id)
    if radius and map_projection:
        unlocated_ids = list(
            session.scalars(
                unlocated.order_by(Race.start_date, Race.id.collate("C"))
                .offset(offset)
                .limit(query.limit)
            )
        )
    next_offset = offset + query.limit
    common = {
        "contract_version": "1.0.0",
        "catalog_version": version,
        "total": total,
        "next_cursor": encode_cursor(version, query.filter_hash, next_offset)
        if next_offset < universe
        else None,
        "coverage": coverage_document(session, state),
    }
    return (
        {
            **common,
            "type": "FeatureCollection",
            "features": features,
            "unlocated_ids": unlocated_ids,
        }
        if map_projection
        else {**common, "items": items, "unlocated_count": unlocated_count}
    )


def select_page(engine, query, *, map_projection=False):
    with engine.connect() as connection:
        default_isolation = connection.default_isolation_level
        connection.execution_options(isolation_level="REPEATABLE READ", postgresql_readonly=True)
        try:
            with Session(connection) as session, session.begin():
                return _read(session, query, map_projection=map_projection)
        finally:
            connection.execution_options(
                isolation_level=default_isolation, postgresql_readonly=False
            )
