"""Private ICS metadata retained for each account/scope until either is purged."""

import sqlalchemy as sa
from alembic import op

revision = "a74d915e3c02"
down_revision = "f61d338ab204"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personal_calendar_event_store",
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("stamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "sequence BETWEEN 0 AND 2147483647",
            name=op.f("ck_personal_calendar_event_store_sequence"),
        ),
        sa.CheckConstraint(
            "fingerprint ~ '^[a-f0-9]{64}$'",
            name=op.f("ck_personal_calendar_event_store_fingerprint"),
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            ondelete="CASCADE",
            name=op.f("fk_personal_calendar_event_store_account_id_account"),
        ),
        sa.ForeignKeyConstraint(
            ["scope_id"],
            ["entry_scope.id"],
            ondelete="CASCADE",
            name=op.f("fk_personal_calendar_event_store_scope_id_entry_scope"),
        ),
        sa.PrimaryKeyConstraint(
            "account_id", "scope_id", name=op.f("pk_personal_calendar_event_store")
        ),
    )
    op.create_index(
        "ix_personal_calendar_event_store_scope_id", "personal_calendar_event_store", ["scope_id"]
    )


def downgrade():
    op.drop_index(
        "ix_personal_calendar_event_store_scope_id", table_name="personal_calendar_event_store"
    )
    op.drop_table("personal_calendar_event_store")
