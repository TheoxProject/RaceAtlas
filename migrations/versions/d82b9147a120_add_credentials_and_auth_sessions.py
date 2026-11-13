"""Private verified credentials and server sessions; no HTTP authentication routes."""

import sqlalchemy as sa
from alembic import op

revision = "d82b9147a120"
down_revision = "c40a7162b901"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_credential",
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "session_version >= 1", name=op.f("ck_password_credential_session_version")
        ),
        sa.CheckConstraint(
            "length(password_hash) BETWEEN 1 AND 512",
            name=op.f("ck_password_credential_password_hash"),
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            ondelete="CASCADE",
            name=op.f("fk_password_credential_account_id_account"),
        ),
        sa.PrimaryKeyConstraint("account_id", name=op.f("pk_password_credential")),
    )
    op.create_table(
        "auth_session",
        sa.Column("token_digest", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("session_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "token_digest ~ '^[a-f0-9]{64}$'", name=op.f("ck_auth_session_token_digest")
        ),
        sa.CheckConstraint("session_version >= 1", name=op.f("ck_auth_session_session_version")),
        sa.CheckConstraint(
            "expires_at > created_at AND last_seen_at >= created_at AND last_seen_at < expires_at",
            name=op.f("ck_auth_session_time_order"),
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["password_credential.account_id"],
            ondelete="CASCADE",
            name=op.f("fk_auth_session_account_id_password_credential"),
        ),
        sa.PrimaryKeyConstraint("token_digest", name=op.f("pk_auth_session")),
    )
    op.create_index(op.f("ix_auth_session_account_id"), "auth_session", ["account_id"])


def downgrade():
    op.drop_index(op.f("ix_auth_session_account_id"), table_name="auth_session")
    op.drop_table("auth_session")
    op.drop_table("password_credential")
