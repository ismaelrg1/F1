"""add user public id and schedule baselines

Revision ID: 4b4b2bfb5f42
Revises: 7387b5553989
Create Date: 2026-03-26 00:00:00.000000
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "4b4b2bfb5f42"
down_revision = "7387b5553989"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="auth",
    )

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id FROM auth.users")).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE auth.users SET public_id = :public_id WHERE id = :id"),
            {"public_id": uuid4(), "id": row.id},
        )

    op.alter_column("users", "public_id", nullable=False, schema="auth")
    op.create_unique_constraint("uq_users_public_id", "users", ["public_id"], schema="auth")
    op.create_index("ix_users_public_id", "users", ["public_id"], unique=False, schema="auth")

    op.add_column(
        "race_events",
        sa.Column("scheduled_event_start", sa.DateTime(timezone=True), nullable=True),
        schema="competition",
    )
    op.add_column(
        "race_events",
        sa.Column("scheduled_event_end", sa.DateTime(timezone=True), nullable=True),
        schema="competition",
    )
    op.execute(
        sa.text(
            """
            UPDATE competition.race_events
            SET scheduled_event_start = event_start,
                scheduled_event_end = event_end
            """
        )
    )

    op.add_column(
        "event_sessions",
        sa.Column("scheduled_start_datetime", sa.DateTime(timezone=True), nullable=True),
        schema="competition",
    )
    op.add_column(
        "event_sessions",
        sa.Column("scheduled_lock_cutoff", sa.DateTime(timezone=True), nullable=True),
        schema="competition",
    )
    op.execute(
        sa.text(
            """
            UPDATE competition.event_sessions
            SET scheduled_start_datetime = start_datetime,
                scheduled_lock_cutoff = lock_cutoff
            """
        )
    )

    op.add_column(
        "testing_events",
        sa.Column("scheduled_event_start", sa.DateTime(timezone=True), nullable=True),
        schema="competition",
    )
    op.add_column(
        "testing_events",
        sa.Column("scheduled_event_end", sa.DateTime(timezone=True), nullable=True),
        schema="competition",
    )
    op.execute(
        sa.text(
            """
            UPDATE competition.testing_events
            SET scheduled_event_start = event_start,
                scheduled_event_end = event_end
            """
        )
    )


def downgrade() -> None:
    op.drop_column("testing_events", "scheduled_event_end", schema="competition")
    op.drop_column("testing_events", "scheduled_event_start", schema="competition")
    op.drop_column("event_sessions", "scheduled_lock_cutoff", schema="competition")
    op.drop_column("event_sessions", "scheduled_start_datetime", schema="competition")
    op.drop_column("race_events", "scheduled_event_end", schema="competition")
    op.drop_column("race_events", "scheduled_event_start", schema="competition")

    op.drop_index("ix_users_public_id", table_name="users", schema="auth")
    op.drop_constraint("uq_users_public_id", "users", schema="auth", type_="unique")
    op.drop_column("users", "public_id", schema="auth")
