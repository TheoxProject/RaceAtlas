"""Bounded, independent HTTP auth admission; contains only pseudonymous counters."""

import sqlalchemy as sa
from alembic import op

revision = "f61d338ab204"
down_revision = "e95c0278b431"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_admission_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.BigInteger(), nullable=False),
        sa.Column("denied", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("id = 1", name=op.f("ck_auth_admission_state_singleton")),
        sa.CheckConstraint(
            "accepted >= 0 AND denied >= 0", name=op.f("ck_auth_admission_state_counts")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_admission_state")),
    )
    op.create_table(
        "auth_admission_bucket",
        sa.Column("namespace", sa.String(12), nullable=False),
        sa.Column("key_digest", sa.String(64), nullable=False),
        sa.Column("admissions", sa.ARRAY(sa.DateTime(timezone=True)), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "namespace IN ('global','peer','address')",
            name=op.f("ck_auth_admission_bucket_namespace"),
        ),
        sa.CheckConstraint(
            "key_digest ~ '^[a-f0-9]{64}$'", name=op.f("ck_auth_admission_bucket_key_digest")
        ),
        sa.CheckConstraint(
            "cardinality(admissions) BETWEEN 1 AND 100",
            name=op.f("ck_auth_admission_bucket_admissions"),
        ),
        sa.PrimaryKeyConstraint("namespace", "key_digest", name=op.f("pk_auth_admission_bucket")),
    )
    op.create_index("ix_auth_admission_bucket_expires_at", "auth_admission_bucket", ["expires_at"])


def downgrade():
    op.drop_index("ix_auth_admission_bucket_expires_at", table_name="auth_admission_bucket")
    op.drop_table("auth_admission_bucket")
    op.drop_table("auth_admission_state")
