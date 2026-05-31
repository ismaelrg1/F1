"""add testing event session support to powerups

Revision ID: 7d4d1cb2c1aa
Revises: 8820187e0920
Create Date: 2026-05-31 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d4d1cb2c1aa"
down_revision = "8820187e0920"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "powerup_restrictions",
        sa.Column("testing_event_session_id", sa.Integer(), nullable=True),
        schema="powerups",
    )
    op.create_foreign_key(
        None,
        "powerup_restrictions",
        "testing_event_sessions",
        ["testing_event_session_id"],
        ["id"],
        source_schema="powerups",
        referent_schema="competition",
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_powerup_restrictions_testing_session_id",
        "powerup_restrictions",
        ["testing_event_session_id"],
        unique=False,
        schema="powerups",
    )
    op.drop_index(
        "uq_powerup_restrictions_ctx_nosession",
        table_name="powerup_restrictions",
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
    op.drop_index(
        "uq_powerup_restrictions_ctx_session",
        table_name="powerup_restrictions",
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.create_index(
        "uq_powerup_restrictions_ctx_nosession",
        "powerup_restrictions",
        ["powerup_id", "bet_context_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.create_index(
        "uq_powerup_restrictions_ctx_event_session",
        "powerup_restrictions",
        ["powerup_id", "bet_context_id", "event_session_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NOT NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.create_index(
        "uq_powerup_restrictions_ctx_testing_session",
        "powerup_restrictions",
        ["powerup_id", "bet_context_id", "testing_event_session_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
        ),
    )
    op.create_check_constraint(
        "ck_powerup_restrictions_single_session_scope",
        "powerup_restrictions",
        "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
        schema="powerups",
    )

    op.add_column(
        "powerup_uses",
        sa.Column("testing_event_session_id", sa.Integer(), nullable=True),
        schema="powerups",
    )
    op.create_foreign_key(
        None,
        "powerup_uses",
        "testing_event_sessions",
        ["testing_event_session_id"],
        ["id"],
        source_schema="powerups",
        referent_schema="competition",
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_powerup_uses_testing_event_session_id",
        "powerup_uses",
        ["testing_event_session_id"],
        unique=False,
        schema="powerups",
    )
    op.drop_index(
        "uq_powerup_uses_user_context_powerup",
        table_name="powerup_uses",
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
    op.drop_index(
        "uq_powerup_uses_user_session_powerup",
        table_name="powerup_uses",
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.create_index(
        "uq_powerup_uses_user_context_powerup",
        "powerup_uses",
        ["user_id", "group_id", "bet_context_id", "powerup_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.create_index(
        "uq_powerup_uses_user_event_session_powerup",
        "powerup_uses",
        ["user_id", "group_id", "bet_context_id", "event_session_id", "powerup_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NOT NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.create_index(
        "uq_powerup_uses_user_testing_session_powerup",
        "powerup_uses",
        ["user_id", "group_id", "bet_context_id", "testing_event_session_id", "powerup_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
        ),
    )
    op.create_check_constraint(
        "ck_powerup_uses_testing_session_requires_context",
        "powerup_uses",
        "testing_event_session_id IS NULL OR bet_context_id IS NOT NULL",
        schema="powerups",
    )
    op.create_check_constraint(
        "ck_powerup_uses_single_session_scope",
        "powerup_uses",
        "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
        schema="powerups",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_powerup_uses_single_session_scope",
        "powerup_uses",
        schema="powerups",
        type_="check",
    )
    op.drop_constraint(
        "ck_powerup_uses_testing_session_requires_context",
        "powerup_uses",
        schema="powerups",
        type_="check",
    )
    op.drop_index(
        "uq_powerup_uses_user_testing_session_powerup",
        table_name="powerup_uses",
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
        ),
    )
    op.drop_index(
        "uq_powerup_uses_user_event_session_powerup",
        table_name="powerup_uses",
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NOT NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.drop_index(
        "uq_powerup_uses_user_context_powerup",
        table_name="powerup_uses",
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.create_index(
        "uq_powerup_uses_user_context_powerup",
        "powerup_uses",
        ["user_id", "group_id", "bet_context_id", "powerup_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
    op.create_index(
        "uq_powerup_uses_user_session_powerup",
        "powerup_uses",
        ["user_id", "group_id", "bet_context_id", "event_session_id", "powerup_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "ix_powerup_uses_testing_event_session_id",
        table_name="powerup_uses",
        schema="powerups",
    )
    op.drop_constraint(None, "powerup_uses", schema="powerups", type_="foreignkey")
    op.drop_column("powerup_uses", "testing_event_session_id", schema="powerups")

    op.drop_constraint(
        "ck_powerup_restrictions_single_session_scope",
        "powerup_restrictions",
        schema="powerups",
        type_="check",
    )
    op.drop_index(
        "uq_powerup_restrictions_ctx_testing_session",
        table_name="powerup_restrictions",
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
        ),
    )
    op.drop_index(
        "uq_powerup_restrictions_ctx_event_session",
        table_name="powerup_restrictions",
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NOT NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.drop_index(
        "uq_powerup_restrictions_ctx_nosession",
        table_name="powerup_restrictions",
        schema="powerups",
        postgresql_where=sa.text(
            "event_session_id IS NULL AND testing_event_session_id IS NULL"
        ),
    )
    op.create_index(
        "uq_powerup_restrictions_ctx_nosession",
        "powerup_restrictions",
        ["powerup_id", "bet_context_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
    op.create_index(
        "uq_powerup_restrictions_ctx_session",
        "powerup_restrictions",
        ["powerup_id", "bet_context_id", "event_session_id"],
        unique=True,
        schema="powerups",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "ix_powerup_restrictions_testing_session_id",
        table_name="powerup_restrictions",
        schema="powerups",
    )
    op.drop_constraint(None, "powerup_restrictions", schema="powerups", type_="foreignkey")
    op.drop_column(
        "powerup_restrictions",
        "testing_event_session_id",
        schema="powerups",
    )
