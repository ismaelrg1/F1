"""add google_sub to auth.users

Revision ID: 8b6f7c2a1d4e
Revises: 5f2c7b0b1d1a
Create Date: 2026-03-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b6f7c2a1d4e"
down_revision: Union[str, Sequence[str], None] = "5f2c7b0b1d1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("google_sub", sa.String(length=255), nullable=True),
        schema="auth",
    )
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=False, schema="auth")
    op.create_unique_constraint("uq_auth_users_google_sub", "users", ["google_sub"], schema="auth")


def downgrade() -> None:
    op.drop_constraint("uq_auth_users_google_sub", "users", schema="auth", type_="unique")
    op.drop_index("ix_users_google_sub", table_name="users", schema="auth")
    op.drop_column("users", "google_sub", schema="auth")
