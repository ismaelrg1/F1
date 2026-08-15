"""add template item scoring overrides

Revision ID: 28ae01b6e851
Revises: 464499485096
Create Date: 2026-08-14 10:53:09.872215
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '28ae01b6e851'
down_revision = '464499485096'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bet_template_items",
        sa.Column("override_points", sa.Numeric(), nullable=True),
        schema="betting",
    )
    op.add_column(
        "bet_template_items",
        sa.Column(
            "override_constraints_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        schema="betting",
    )
    op.create_check_constraint(
        "ck_bet_template_items_override_points_nonneg",
        "bet_template_items",
        "override_points IS NULL OR override_points >= 0",
        schema="betting",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_bet_template_items_override_points_nonneg",
        "bet_template_items",
        schema="betting",
        type_="check",
    )
    op.drop_column("bet_template_items", "override_constraints_json", schema="betting")
    op.drop_column("bet_template_items", "override_points", schema="betting")
