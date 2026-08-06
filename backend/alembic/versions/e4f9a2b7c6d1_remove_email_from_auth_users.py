"""remove email from auth users

Revision ID: e4f9a2b7c6d1
Revises: 07c0f042b979
Create Date: 2026-08-06 18:20:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "e4f9a2b7c6d1"
down_revision = "07c0f042b979"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_users_email", "users", schema="auth", type_="unique")
    op.execute("ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS ck_users_email_minlen")
    op.drop_column("users", "email", schema="auth")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email", postgresql.CITEXT(), nullable=True),
        schema="auth",
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"], schema="auth")
