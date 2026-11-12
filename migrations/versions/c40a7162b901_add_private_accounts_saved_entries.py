"""Add private account identities and saved entry scopes (not authentication)."""

import sqlalchemy as sa
from alembic import op

revision = "c40a7162b901"
down_revision = "b7f4208ac112"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("email_normalized", sa.String(254), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "email_normalized = lower(btrim(email_normalized))",
            name=op.f("ck_account_email_normalized"),
        ),
        sa.CheckConstraint(
            "email_normalized ~ '^[^[:space:][:cntrl:]@]+@[^[:space:][:cntrl:]@]+$'",
            name=op.f("ck_account_email_shape"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account")),
        sa.UniqueConstraint("email_normalized", name=op.f("uq_account_email_normalized")),
    )
    op.create_table(
        "saved_entry",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('interested','planned','registered','completed')",
            name=op.f("ck_saved_entry_status"),
        ),
        sa.CheckConstraint("revision >= 1", name=op.f("ck_saved_entry_revision")),
        sa.CheckConstraint("updated_at >= created_at", name=op.f("ck_saved_entry_time_order")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            ondelete="CASCADE",
            name=op.f("fk_saved_entry_account_id_account"),
        ),
        sa.ForeignKeyConstraint(
            ["scope_id"],
            ["entry_scope.id"],
            ondelete="RESTRICT",
            name=op.f("fk_saved_entry_scope_id_entry_scope"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_saved_entry")),
        sa.UniqueConstraint("account_id", "scope_id", name=op.f("uq_saved_entry_account_id")),
    )
    op.create_index(op.f("ix_saved_entry_scope_id"), "saved_entry", ["scope_id"])


def downgrade():
    op.drop_index(op.f("ix_saved_entry_scope_id"), table_name="saved_entry")
    op.drop_table("saved_entry")
    op.drop_table("account")
