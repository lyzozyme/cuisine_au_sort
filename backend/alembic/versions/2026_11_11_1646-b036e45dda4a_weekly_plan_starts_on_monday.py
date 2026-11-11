"""weekly plan starts on monday

Écrite à la main : l'autogénération d'Alembic ne détecte pas les contraintes CHECK.

Revision ID: b036e45dda4a
Revises: fa8157156f4a
Create Date: 2026-11-11 16:46:48.401204

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b036e45dda4a"
down_revision: str | Sequence[str] | None = "fa8157156f4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        op.f("ck_weekly_plans_week_start_is_monday"),
        "weekly_plans",
        "EXTRACT(ISODOW FROM week_start) = 1",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("ck_weekly_plans_week_start_is_monday"), "weekly_plans", type_="check")
