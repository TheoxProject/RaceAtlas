"""Add transactional catalogue revision and extension-free normalized search."""

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "b7f4208ac112"
down_revision = "8a95eb41f220"
branch_labels = None
depends_on = None

TABLES = (
    "race",
    "race_type",
    "source_record",
    "commune",
    "entry_scope",
    "eligibility_rule",
    "rule_category",
    "category",
    "import_run",
    "import_window",
)


def upgrade():
    op.add_column(
        "import_run", sa.Column("catalog_order", sa.BigInteger(), sa.Identity(), nullable=False)
    )
    op.create_unique_constraint(
        op.f("uq_import_run_catalog_order"), "import_run", ["catalog_order"]
    )
    state = op.create_table(
        "catalog_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("epoch", sa.String(32), nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("audit_floor", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("id = 1", name=op.f("ck_catalog_state_singleton")),
        sa.CheckConstraint("revision >= 0", name=op.f("ck_catalog_state_revision")),
        sa.CheckConstraint("epoch ~ '^[a-f0-9]{32}$'", name=op.f("ck_catalog_state_epoch")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_catalog_state")),
    )
    floor = op.get_bind().scalar(sa.text("SELECT COALESCE(MAX(catalog_order), 0) FROM import_run"))
    op.bulk_insert(state, [{"id": 1, "epoch": uuid4().hex, "revision": 0, "audit_floor": floor}])
    op.execute("""
        CREATE FUNCTION catalog_bump_revision() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            UPDATE catalog_state SET revision = revision + 1 WHERE id = 1;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'catalog_state_missing';
            END IF;
            RETURN NULL;
        END
        $$
    """)
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER catalog_revision_{table} "
            f"AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION catalog_bump_revision()"
        )
    # NFD/Latin accent normalization; no unaccent/trigram/PostGIS extension or grant.
    op.execute(r"""
        CREATE FUNCTION catalog_normalize(value text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
            SELECT btrim(regexp_replace(lower(translate(
                regexp_replace(normalize(coalesce(value, ''), NFD), U&'[\0300-\036f]', '', 'g'),
                'ŒÆØÐÞẞ', 'œæøðþß'
            )), '[[:space:]]+', ' ', 'g'))
        $$
    """)


def downgrade():
    op.execute("DROP FUNCTION catalog_normalize(text)")
    for table in reversed(TABLES):
        op.execute(f"DROP TRIGGER catalog_revision_{table} ON {table}")
    op.execute("DROP FUNCTION catalog_bump_revision()")
    op.drop_table("catalog_state")
    op.drop_constraint(op.f("uq_import_run_catalog_order"), "import_run", type_="unique")
    op.drop_column("import_run", "catalog_order")
