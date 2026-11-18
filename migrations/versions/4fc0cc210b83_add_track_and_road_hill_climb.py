"""Extend the discipline and road type domains without reclassifying races."""

from alembic import op

revision = "4fc0cc210b83"
down_revision = "b806e44f7901"
branch_labels = None
depends_on = None


def _replace_checks(*, extra_discipline, extra_road_type):
    checks = (
        (
            "race",
            "ck_race_discipline",
            "discipline IN ('road','gravel','mtb','cyclocross'" + extra_discipline + ")",
        ),
        (
            "race_type",
            "ck_race_type_code",
            "code IN ('road_race','time_trial','gravel_race','xco','enduro','downhill','cyclocross'"
            + extra_road_type
            + ")",
        ),
        (
            "race_type",
            "ck_race_type_discipline_type",
            "(discipline = 'road' AND code IN ('road_race','time_trial'"
            + extra_road_type
            + ")) OR "
            "(discipline = 'gravel' AND code = 'gravel_race') OR "
            "(discipline = 'mtb' AND code IN ('xco','enduro','downhill')) OR "
            "(discipline = 'cyclocross' AND code = 'cyclocross')",
        ),
    )
    for table, name, expression in checks:
        op.drop_constraint(op.f(name), table, type_="check")
        op.create_check_constraint(op.f(name), table, expression)


def upgrade():
    _replace_checks(extra_discipline=",'track'", extra_road_type=",'hill_climb'")


def downgrade():
    # PostgreSQL rejects the downgrade transaction if existing rows use either new value.
    _replace_checks(extra_discipline="", extra_road_type="")
