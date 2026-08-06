"""add team color

Revision ID: 07c0f042b979
Revises: 7d4d1cb2c1aa
Create Date: 2026-08-06 16:26:58.455937
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07c0f042b979'
down_revision = '7d4d1cb2c1aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column(
            "color",
            sa.String(length=7),
            nullable=False,
            server_default=sa.text("'#000000'"),
        ),
        schema="competition",
    )
    op.create_check_constraint(
        "ck_teams_color_format",
        "teams",
        "color ~ '^#[0-9A-Fa-f]{6}$'",
        schema="competition",
    )
    op.alter_column("teams", "color", server_default=None, schema="competition")


def downgrade() -> None:
    op.drop_constraint(
        "ck_teams_color_format",
        "teams",
        schema="competition",
        type_="check",
    )
    op.drop_column("teams", "color", schema="competition")
