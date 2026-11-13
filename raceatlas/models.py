"""Relational foundation; synthetic IDs are accepted, new IDs default to UUIDs."""

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    MetaData,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

DEPARTMENTS = "'01','03','07','15','26','38','42','43','63','69','73','74'"


def opaque_id():
    return str(uuid4())


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class CatalogState(Base):
    """One persistent revision, transactionally advanced by relevant table statements."""

    __tablename__ = "catalog_state"
    __table_args__ = (
        CheckConstraint("id = 1", name="singleton"),
        CheckConstraint("revision >= 0", name="revision"),
        CheckConstraint("epoch ~ '^[a-f0-9]{32}$'", name="epoch"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    epoch: Mapped[str] = mapped_column(String(32))
    revision: Mapped[int] = mapped_column(BigInteger)
    audit_floor: Mapped[int] = mapped_column(BigInteger)


class Competition(Base):
    __tablename__ = "competition"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    grouping_evidence: Mapped[str] = mapped_column(String, nullable=False)


class Commune(Base):
    __tablename__ = "commune"
    __table_args__ = (
        UniqueConstraint("id", "department"),
        CheckConstraint(f"department IN ({DEPARTMENTS})", name="department"),
        CheckConstraint("precision = 'commune_center'", name="precision"),
        CheckConstraint(
            "provenance IN ('synthetic','geo_api','verified_source')", name="provenance"
        ),
        CheckConstraint("(longitude IS NULL) = (latitude IS NULL)", name="coordinate_pair"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    insee_code: Mapped[str | None] = mapped_column(String(5), unique=True)
    name: Mapped[str] = mapped_column(String)
    department: Mapped[str] = mapped_column(String(2), index=True)
    longitude: Mapped[float | None]
    latitude: Mapped[float | None]
    precision: Mapped[str] = mapped_column(String, default="commune_center")
    provenance: Mapped[str] = mapped_column(String)
    geocoded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Race(Base):
    __tablename__ = "race"
    __table_args__ = (
        UniqueConstraint("id", "discipline"),
        ForeignKeyConstraint(["commune_id", "department"], ["commune.id", "commune.department"]),
        CheckConstraint("end_date >= start_date", name="date_order"),
        CheckConstraint(f"department IN ({DEPARTMENTS})", name="department"),
        CheckConstraint("discipline IN ('road','gravel','mtb','cyclocross')", name="discipline"),
        CheckConstraint("status IN ('scheduled','cancelled','postponed','unknown')", name="status"),
        CheckConstraint("source_presence IN ('present','missing','to_verify')", name="presence"),
        CheckConstraint("revision >= 1", name="revision"),
        Index("ix_race_dates", "start_date", "end_date"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    competition_id: Mapped[str | None] = mapped_column(ForeignKey("competition.id"))
    commune_id: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String)
    discipline: Mapped[str] = mapped_column(String, index=True)
    organizer: Mapped[str | None] = mapped_column(String)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    department: Mapped[str] = mapped_column(String(2), index=True)
    status: Mapped[str] = mapped_column(String)
    source_presence: Mapped[str] = mapped_column(String)
    revision: Mapped[int] = mapped_column(default=1)
    commune: Mapped[Commune | None] = relationship()
    types: Mapped[list["RaceType"]] = relationship(
        cascade="all, delete-orphan", order_by="RaceType.code"
    )
    source: Mapped["SourceRecord"] = relationship(cascade="all, delete-orphan", uselist=False)
    scopes: Mapped[list["EntryScope"]] = relationship(
        cascade="all, delete-orphan", order_by="EntryScope.position"
    )


class RaceType(Base):
    __tablename__ = "race_type"
    __table_args__ = (
        ForeignKeyConstraint(["race_id", "discipline"], ["race.id", "race.discipline"]),
        CheckConstraint(
            "code IN ('road_race','time_trial','gravel_race',"
            "'xco','enduro','downhill','cyclocross')",
            name="code",
        ),
        CheckConstraint(
            "(discipline = 'road' AND code IN ('road_race','time_trial')) OR "
            "(discipline = 'gravel' AND code = 'gravel_race') OR "
            "(discipline = 'mtb' AND code IN ('xco','enduro','downhill')) OR "
            "(discipline = 'cyclocross' AND code = 'cyclocross')",
            name="discipline_type",
        ),
    )
    race_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    discipline: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(String, primary_key=True)


class SourceRecord(Base):
    __tablename__ = "source_record"
    __table_args__ = (
        UniqueConstraint("provider", "source_season", "race_number"),
        CheckConstraint("provider IN ('synthetic','ffc')", name="provider"),
        CheckConstraint("source_season BETWEEN 2000 AND 2200", name="season"),
        CheckConstraint("presence_checked_at >= checked_at", name="presence_freshness"),
    )
    race_id: Mapped[str] = mapped_column(ForeignKey("race.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String)
    source_season: Mapped[int]
    race_number: Mapped[str] = mapped_column(String)
    source_url: Mapped[str] = mapped_column(String)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Nullable for legacy/synthetic ORM writers; importer falls back to checked_at.
    # Unlike checked_at, this marker also advances on a controlled source absence.
    presence_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EntryScope(Base):
    __tablename__ = "entry_scope"
    __table_args__ = (
        CheckConstraint("kind IN ('entry_list','race')", name="kind"),
        CheckConstraint(
            "identity_status IN ('verified','unverified','needs_review')", name="identity"
        ),
        CheckConstraint(
            "eligibility_status IN ('confirmed','unknown','ambiguous')", name="eligibility"
        ),
        UniqueConstraint("race_id", "source_list_id"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    race_id: Mapped[str] = mapped_column(ForeignKey("race.id"), index=True)
    position: Mapped[int]
    kind: Mapped[str] = mapped_column(String)
    source_list_id: Mapped[str | None] = mapped_column(String)
    identity_status: Mapped[str] = mapped_column(String)
    eligibility_status: Mapped[str] = mapped_column(String)
    raw_label: Mapped[str] = mapped_column(String)
    rules: Mapped[list["EligibilityRule"]] = relationship(
        cascade="all, delete-orphan", order_by="EligibilityRule.position"
    )


class Category(Base):
    __tablename__ = "category"
    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String)


class EligibilityRule(Base):
    __tablename__ = "eligibility_rule"
    __table_args__ = (
        CheckConstraint("sex IN ('men','women','any','unknown')", name="sex"),
        CheckConstraint("min_age BETWEEN 0 AND 120", name="min_age"),
        CheckConstraint("max_age BETWEEN 0 AND 120", name="max_age"),
        CheckConstraint("max_age >= min_age", name="age_order"),
        CheckConstraint(
            "age_reference IN ('season_end','event_date','unknown')", name="age_reference"
        ),
        CheckConstraint("age_season BETWEEN 2000 AND 2200", name="age_season"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    scope_id: Mapped[str] = mapped_column(ForeignKey("entry_scope.id"), index=True)
    position: Mapped[int]
    sex: Mapped[str] = mapped_column(String)
    min_age: Mapped[int | None]
    max_age: Mapped[int | None]
    age_reference: Mapped[str] = mapped_column(String)
    age_season: Mapped[int | None]
    engagers: Mapped[list[str]] = mapped_column(JSON)
    other_text: Mapped[str | None] = mapped_column(String)
    raw_label: Mapped[str] = mapped_column(String)
    evidence_id: Mapped[str] = mapped_column(String(64))
    normalization_version: Mapped[str] = mapped_column(String, default="1.0.0")
    categories: Mapped[list["RuleCategory"]] = relationship(
        cascade="all, delete-orphan", order_by="RuleCategory.position"
    )


class RuleCategory(Base):
    __tablename__ = "rule_category"
    rule_id: Mapped[str] = mapped_column(ForeignKey("eligibility_rule.id"), primary_key=True)
    category_code: Mapped[str] = mapped_column(ForeignKey("category.code"), primary_key=True)
    position: Mapped[int]


class ImportRun(Base):
    __tablename__ = "import_run"
    __table_args__ = (
        CheckConstraint("status IN ('running','success','partial','failed')", name="status"),
        CheckConstraint("finished_at >= started_at", name="time_order"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    catalog_order: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String)
    parser_version: Mapped[str] = mapped_column(String)
    synthetic: Mapped[bool]
    missing_marked: Mapped[int] = mapped_column(default=0)


class ImportWindow(Base):
    __tablename__ = "import_window"
    __table_args__ = (
        CheckConstraint("status IN ('success','incomplete','partial','failed')", name="status"),
        CheckConstraint("displayed_count >= 0 AND distinct_keys >= 0", name="counts"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("import_run.id"), index=True)
    requested_from: Mapped[date] = mapped_column(Date)
    requested_to: Mapped[date] = mapped_column(Date)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date] = mapped_column(Date)
    requested_department: Mapped[str] = mapped_column(String(2))
    effective_department: Mapped[str | None] = mapped_column(String(2))
    displayed_count: Mapped[int]
    distinct_keys: Mapped[int]
    status: Mapped[str] = mapped_column(String)
    diagnostics: Mapped[list[str]] = mapped_column(JSON)
    source_url: Mapped[str] = mapped_column(String)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ImportItem(Base):
    __tablename__ = "import_item"
    __table_args__ = (
        UniqueConstraint("window_id", "source_season", "race_number"),
        CheckConstraint(
            "status IN ('created','updated','unchanged','review','error')", name="status"
        ),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    window_id: Mapped[str] = mapped_column(ForeignKey("import_window.id"), index=True)
    source_season: Mapped[int]
    race_number: Mapped[str] = mapped_column(String)
    race_id: Mapped[str | None] = mapped_column(ForeignKey("race.id"))
    status: Mapped[str] = mapped_column(String)
    diagnostic: Mapped[str | None] = mapped_column(String)
    # Only normalized business facts needed for review, never HTML or participant zones.
    observed: Mapped[dict | None] = mapped_column(JSON)


class SourceAlias(Base):
    __tablename__ = "source_alias"
    __table_args__ = (
        UniqueConstraint("provider", "source_season", "race_number"),
        CheckConstraint("provider = 'ffc'", name="provider"),
        CheckConstraint("source_season BETWEEN 2000 AND 2200", name="season"),
        CheckConstraint("length(trim(evidence_id)) > 0", name="evidence"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    provider: Mapped[str] = mapped_column(String, default="ffc")
    source_season: Mapped[int]
    race_number: Mapped[str] = mapped_column(String)
    race_id: Mapped[str] = mapped_column(ForeignKey("race.id"), index=True)
    evidence_id: Mapped[str] = mapped_column(String)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceRevision(Base):
    __tablename__ = "source_revision"
    __table_args__ = (
        UniqueConstraint("race_id", "revision"),
        CheckConstraint("revision >= 1", name="revision"),
        CheckConstraint("length(business_hash) = 64", name="hash"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    race_id: Mapped[str] = mapped_column(ForeignKey("race.id"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("import_run.id"))
    revision: Mapped[int]
    business_hash: Mapped[str] = mapped_column(String(64))
    facts: Mapped[dict] = mapped_column(JSON)
    normalization_version: Mapped[str] = mapped_column(String)
    source_url: Mapped[str] = mapped_column(String)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class GeocodeCache(Base):
    __tablename__ = "geocode_cache"
    __table_args__ = (
        UniqueConstraint("provider", "provider_version", "query_key"),
        CheckConstraint("status IN ('positive','negative','error')", name="status"),
        CheckConstraint("expires_at > checked_at", name="expiry"),
        CheckConstraint(
            "(status = 'positive' AND commune_id IS NOT NULL) OR "
            "(status IN ('negative','error') AND commune_id IS NULL)",
            name="result",
        ),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    provider: Mapped[str] = mapped_column(String)
    provider_version: Mapped[str] = mapped_column(String)
    query_key: Mapped[str] = mapped_column(String(64))
    query: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String)
    commune_id: Mapped[str | None] = mapped_column(ForeignKey("commune.id"))
    diagnostic: Mapped[str | None] = mapped_column(String)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PrivateUTCDateTime(TypeDecorator):
    """Keep PostgreSQL timestamptz while exposing private timestamps as aware UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("Private timestamps require timezone-aware values.")
            return value.astimezone(timezone.utc)
        return None

    def process_result_value(self, value, dialect):
        return value.astimezone(timezone.utc) if value is not None else None


class Account(Base):
    """Private identity only; no credentials or authenticated session in ACC-01."""

    __tablename__ = "account"
    __table_args__ = (
        UniqueConstraint("email_normalized"),
        CheckConstraint(
            "email_normalized = lower(btrim(email_normalized))", name="email_normalized"
        ),
        CheckConstraint(
            "email_normalized ~ '^[^[:space:][:cntrl:]@]+@[^[:space:][:cntrl:]@]+$'",
            name="email_shape",
        ),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    email_normalized: Mapped[str] = mapped_column(String(254))
    created_at: Mapped[datetime] = mapped_column(PrivateUTCDateTime(), server_default=func.now())


class SavedEntry(Base):
    __tablename__ = "saved_entry"
    __table_args__ = (
        UniqueConstraint("account_id", "scope_id"),
        CheckConstraint(
            "status IN ('interested','planned','registered','completed')", name="status"
        ),
        CheckConstraint("revision >= 1", name="revision"),
        CheckConstraint("updated_at >= created_at", name="time_order"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=opaque_id)
    account_id: Mapped[str] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    scope_id: Mapped[str] = mapped_column(
        ForeignKey("entry_scope.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String)
    revision: Mapped[int] = mapped_column(default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(PrivateUTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(PrivateUTCDateTime(), server_default=func.now())
    scope: Mapped[EntryScope] = relationship()


class PasswordCredential(Base):
    __tablename__ = "password_credential"
    __table_args__ = (
        CheckConstraint("session_version >= 1", name="session_version"),
        CheckConstraint("length(password_hash) BETWEEN 1 AND 512", name="password_hash"),
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    password_hash: Mapped[str] = mapped_column(String(512))
    email_verified_at: Mapped[datetime | None] = mapped_column(PrivateUTCDateTime())
    session_version: Mapped[int] = mapped_column(default=1, server_default="1")


class AuthSession(Base):
    __tablename__ = "auth_session"
    __table_args__ = (
        CheckConstraint("token_digest ~ '^[a-f0-9]{64}$'", name="token_digest"),
        CheckConstraint("session_version >= 1", name="session_version"),
        CheckConstraint(
            "expires_at > created_at AND last_seen_at >= created_at AND last_seen_at < expires_at",
            name="time_order",
        ),
    )
    token_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("password_credential.account_id", ondelete="CASCADE"), index=True
    )
    session_version: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(PrivateUTCDateTime())
    last_seen_at: Mapped[datetime] = mapped_column(PrivateUTCDateTime())
    expires_at: Mapped[datetime] = mapped_column(PrivateUTCDateTime())
