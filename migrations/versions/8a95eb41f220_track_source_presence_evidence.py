"""Track the latest checked presence or controlled absence independently of page freshness."""

import sqlalchemy as sa
from alembic import op

revision = "8a95eb41f220"
down_revision = "65107930ec01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "source_record", sa.Column("presence_checked_at", sa.DateTime(timezone=True), nullable=True)
    )
    # Actual successful window/item evidence distinguishes absence (including ties)
    # from a mere page-check timestamp. Positive observations through ANY alias/window
    # of the same run exclude the candidate absence.
    absence_evidence = """
        SELECT MAX(coverage_window.checked_at)
        FROM import_window AS coverage_window
        JOIN import_run AS run ON run.id = coverage_window.run_id
        JOIN race AS observed_race ON observed_race.id = source.race_id
        WHERE source.provider = 'ffc' AND run.status = 'success'
          AND coverage_window.status = 'success'
          AND coverage_window.effective_department = observed_race.department
          AND observed_race.start_date <= coverage_window.effective_to
          AND observed_race.end_date >= coverage_window.effective_from
          AND NOT EXISTS (
            SELECT 1 FROM import_item AS item
            JOIN import_window AS item_window ON item_window.id = item.window_id
            WHERE item_window.run_id = run.id AND item.race_id = observed_race.id
              AND item.status IN ('created','updated','unchanged')
              AND item.diagnostic IS NULL
          )
    """
    op.execute(
        "UPDATE source_record AS source SET presence_checked_at = "
        "GREATEST(source.checked_at, COALESCE((" + absence_evidence + "), source.checked_at))"
    )
    # Repair legacy false presences only when an actual equal/newer absence exists.
    # No-absence rows also have equal clocks and must remain present.
    op.execute(
        "UPDATE race AS target SET source_presence = 'to_verify' "
        "FROM source_record AS source "
        "WHERE source.race_id = target.id AND source.provider = 'ffc' AND ("
        + absence_evidence
        + ") >= source.checked_at"
    )
    op.create_check_constraint(
        op.f("ck_source_record_presence_freshness"),
        "source_record",
        "presence_checked_at >= checked_at",
    )


def downgrade():
    op.drop_constraint(op.f("ck_source_record_presence_freshness"), "source_record", type_="check")
    op.drop_column("source_record", "presence_checked_at")
