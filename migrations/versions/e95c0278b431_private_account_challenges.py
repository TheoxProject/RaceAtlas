"""Private confirmation/reset proofs and bounded email reservations."""

import sqlalchemy as sa
from alembic import op

revision = "e95c0278b431"
down_revision = "d82b9147a120"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_challenge",
        sa.Column("token_digest", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("purpose", sa.String(12), nullable=False),
        sa.Column("credential_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "purpose IN ('confirmation','reset')", name=op.f("ck_auth_challenge_purpose")
        ),
        sa.CheckConstraint(
            "token_digest ~ '^[a-f0-9]{64}$'", name=op.f("ck_auth_challenge_token_digest")
        ),
        sa.CheckConstraint(
            "credential_version >= 1", name=op.f("ck_auth_challenge_credential_version")
        ),
        sa.CheckConstraint("expires_at > created_at", name=op.f("ck_auth_challenge_time_order")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            ondelete="CASCADE",
            name=op.f("fk_auth_challenge_account_id_account"),
        ),
        sa.PrimaryKeyConstraint("token_digest", name=op.f("pk_auth_challenge")),
        sa.UniqueConstraint("account_id", "purpose", name=op.f("uq_auth_challenge_account_id")),
    )
    op.create_table(
        "email_budget",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("day_count", sa.Integer(), nullable=False),
        sa.Column("month_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("id = 1", name=op.f("ck_email_budget_singleton")),
        sa.CheckConstraint(
            "day_count >= 0 AND month_count >= 0", name=op.f("ck_email_budget_counts")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_budget")),
    )
    op.create_table(
        "email_address_quota",
        sa.Column("address_digest", sa.String(64), nullable=False),
        sa.Column("purpose", sa.String(12), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_admitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("admitted", sa.Integer(), nullable=False),
        sa.Column("admissions", sa.ARRAY(sa.DateTime(timezone=True)), nullable=False),
        sa.CheckConstraint(
            "purpose IN ('confirmation','reset')", name=op.f("ck_email_address_quota_purpose")
        ),
        sa.CheckConstraint(
            "address_digest ~ '^[a-f0-9]{64}$'", name=op.f("ck_email_address_quota_address_digest")
        ),
        sa.CheckConstraint(
            "admitted BETWEEN 1 AND 100 AND cardinality(admissions) = admitted",
            name=op.f("ck_email_address_quota_admitted"),
        ),
        sa.CheckConstraint(
            "expires_at > last_admitted_at AND last_admitted_at >= window_started_at",
            name=op.f("ck_email_address_quota_time_order"),
        ),
        sa.PrimaryKeyConstraint("address_digest", "purpose", name=op.f("pk_email_address_quota")),
    )
    op.create_index("ix_email_address_quota_expires_at", "email_address_quota", ["expires_at"])


def downgrade():
    op.drop_index("ix_email_address_quota_expires_at", table_name="email_address_quota")
    op.drop_table("email_address_quota")
    op.drop_table("email_budget")
    op.drop_table("auth_challenge")
