"""Scoped changes and private notifications owned by current subscriptions."""

import sqlalchemy as sa
from alembic import op

revision = "b806e44f7901"
down_revision = "a74d915e3c02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "saved_entry", sa.Column("notifications_after_sequence", sa.BigInteger(), nullable=True)
    )
    op.execute("UPDATE saved_entry SET notifications_after_sequence = 0")
    op.alter_column("saved_entry", "notifications_after_sequence", nullable=False)
    op.create_check_constraint(
        op.f("ck_saved_entry_notification_baseline"),
        "saved_entry",
        "notifications_after_sequence >= 0",
    )
    op.create_table(
        "race_change",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "race_id", sa.String(64), sa.ForeignKey("race.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("event_key", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("signature", sa.String(64), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.clock_timestamp(),
            nullable=False,
        ),
        sa.UniqueConstraint("race_id", "event_key", name=op.f("uq_race_change_race_id")),
        sa.CheckConstraint("kind IN ('business','presence')", name=op.f("ck_race_change_kind")),
    )
    op.create_table(
        "scope_change",
        sa.Column(
            "change_id",
            sa.String(64),
            sa.ForeignKey("race_change.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "scope_id",
            sa.String(64),
            sa.ForeignKey("entry_scope.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("scope_id", "sequence", name=op.f("uq_scope_change_scope_id")),
        sa.CheckConstraint("sequence >= 1", name=op.f("ck_scope_change_sequence")),
    )
    op.create_table(
        "personal_notification",
        sa.Column("account_id", sa.String(64), primary_key=True),
        sa.Column("change_id", sa.String(64), primary_key=True),
        sa.Column("scope_id", sa.String(64), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.clock_timestamp(),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id", "scope_id"],
            ["saved_entry.account_id", "saved_entry.scope_id"],
            ondelete="CASCADE",
            name=op.f("fk_personal_notification_account_id_saved_entry"),
        ),
        sa.ForeignKeyConstraint(
            ["change_id", "scope_id"],
            ["scope_change.change_id", "scope_change.scope_id"],
            ondelete="CASCADE",
            name=op.f("fk_personal_notification_change_id_scope_change"),
        ),
    )
    op.create_index(
        "ix_personal_notification_account_unread",
        "personal_notification",
        ["account_id", "read_at"],
    )


def downgrade():
    op.drop_index("ix_personal_notification_account_unread", table_name="personal_notification")
    op.drop_table("personal_notification")
    op.drop_table("scope_change")
    op.drop_table("race_change")
    op.drop_constraint(op.f("ck_saved_entry_notification_baseline"), "saved_entry", type_="check")
    op.drop_column("saved_entry", "notifications_after_sequence")
