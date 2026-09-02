"""add less than or equal bet score relation type

Revision ID: 20260902_0001
Revises: 709f75c51f7e
Create Date: 2026-09-02 00:00:00.000000
"""

from alembic import op


revision = "20260902_0001"
down_revision = "709f75c51f7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires the new enum value to be committed before it can
    # be referenced by later SQL data updates.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE betting.bet_score_relation_type_enum "
            "ADD VALUE IF NOT EXISTS 'LESS_THAN_OR_EQUAL'"
        )


def downgrade() -> None:
    # PostgreSQL does not support removing an enum value safely.
    pass
