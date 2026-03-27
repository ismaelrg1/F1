"""add public ids to visible entities

Revision ID: 9e08fef16cb2
Revises: 4b4b2bfb5f42
Create Date: 2026-03-27 00:00:00.000000
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "9e08fef16cb2"
down_revision = "4b4b2bfb5f42"
branch_labels = None
depends_on = None


def _backfill_public_ids(schema: str, table: str) -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text(f"SELECT id FROM {schema}.{table}")).fetchall()
    for row in rows:
        bind.execute(
            sa.text(f"UPDATE {schema}.{table} SET public_id = :public_id WHERE id = :id"),
            {"public_id": uuid4(), "id": row.id},
        )


def upgrade() -> None:
    op.add_column(
        "bet_contexts",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="betting",
    )
    _backfill_public_ids("betting", "bet_contexts")
    op.alter_column("bet_contexts", "public_id", nullable=False, schema="betting")
    op.create_unique_constraint(
        "uq_bet_contexts_public_id",
        "bet_contexts",
        ["public_id"],
        schema="betting",
    )
    op.create_index(
        "ix_bet_contexts_public_id",
        "bet_contexts",
        ["public_id"],
        unique=False,
        schema="betting",
    )

    op.add_column(
        "race_events",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="competition",
    )
    _backfill_public_ids("competition", "race_events")
    op.alter_column("race_events", "public_id", nullable=False, schema="competition")
    op.create_unique_constraint(
        "uq_race_events_public_id",
        "race_events",
        ["public_id"],
        schema="competition",
    )
    op.create_index(
        "ix_race_events_public_id",
        "race_events",
        ["public_id"],
        unique=False,
        schema="competition",
    )

    op.add_column(
        "testing_events",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="competition",
    )
    _backfill_public_ids("competition", "testing_events")
    op.alter_column("testing_events", "public_id", nullable=False, schema="competition")
    op.create_unique_constraint(
        "uq_testing_events_public_id",
        "testing_events",
        ["public_id"],
        schema="competition",
    )
    op.create_index(
        "ix_testing_events_public_id",
        "testing_events",
        ["public_id"],
        unique=False,
        schema="competition",
    )

    op.add_column(
        "event_sessions",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="competition",
    )
    _backfill_public_ids("competition", "event_sessions")
    op.alter_column("event_sessions", "public_id", nullable=False, schema="competition")
    op.create_unique_constraint(
        "uq_event_sessions_public_id",
        "event_sessions",
        ["public_id"],
        schema="competition",
    )
    op.create_index(
        "ix_event_sessions_public_id",
        "event_sessions",
        ["public_id"],
        unique=False,
        schema="competition",
    )

    op.add_column(
        "groups",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="social",
    )
    _backfill_public_ids("social", "groups")
    op.alter_column("groups", "public_id", nullable=False, schema="social")
    op.create_unique_constraint(
        "uq_groups_public_id",
        "groups",
        ["public_id"],
        schema="social",
    )
    op.create_index(
        "ix_groups_public_id",
        "groups",
        ["public_id"],
        unique=False,
        schema="social",
    )

    op.add_column(
        "teams",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="social",
    )
    _backfill_public_ids("social", "teams")
    op.alter_column("teams", "public_id", nullable=False, schema="social")
    op.create_unique_constraint(
        "uq_teams_public_id",
        "teams",
        ["public_id"],
        schema="social",
    )
    op.create_index(
        "ix_teams_public_id",
        "teams",
        ["public_id"],
        unique=False,
        schema="social",
    )


def downgrade() -> None:
    op.drop_index("ix_teams_public_id", table_name="teams", schema="social")
    op.drop_constraint("uq_teams_public_id", "teams", schema="social", type_="unique")
    op.drop_column("teams", "public_id", schema="social")

    op.drop_index("ix_groups_public_id", table_name="groups", schema="social")
    op.drop_constraint("uq_groups_public_id", "groups", schema="social", type_="unique")
    op.drop_column("groups", "public_id", schema="social")

    op.drop_index("ix_event_sessions_public_id", table_name="event_sessions", schema="competition")
    op.drop_constraint(
        "uq_event_sessions_public_id",
        "event_sessions",
        schema="competition",
        type_="unique",
    )
    op.drop_column("event_sessions", "public_id", schema="competition")

    op.drop_index("ix_testing_events_public_id", table_name="testing_events", schema="competition")
    op.drop_constraint(
        "uq_testing_events_public_id",
        "testing_events",
        schema="competition",
        type_="unique",
    )
    op.drop_column("testing_events", "public_id", schema="competition")

    op.drop_index("ix_race_events_public_id", table_name="race_events", schema="competition")
    op.drop_constraint(
        "uq_race_events_public_id",
        "race_events",
        schema="competition",
        type_="unique",
    )
    op.drop_column("race_events", "public_id", schema="competition")

    op.drop_index("ix_bet_contexts_public_id", table_name="bet_contexts", schema="betting")
    op.drop_constraint(
        "uq_bet_contexts_public_id",
        "bet_contexts",
        schema="betting",
        type_="unique",
    )
    op.drop_column("bet_contexts", "public_id", schema="betting")
