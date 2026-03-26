"""add scoring rules table

Revision ID: 5f2c7b0b1d1a
Revises: 8792d0a7d6c0
Create Date: 2026-03-11 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "5f2c7b0b1d1a"
down_revision = "8792d0a7d6c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname = 'scoring_rule_scope_enum'
            AND n.nspname = 'scoring'
        ) THEN
            CREATE TYPE scoring.scoring_rule_scope_enum AS ENUM (
                'GLOBAL',
                'BET_SCORE',
                'CONTEXT',
                'SESSION'
            );
        END IF;
    END $$;
    """)

    scoring_rule_scope_enum = postgresql.ENUM(
        "GLOBAL",
        "BET_SCORE",
        "CONTEXT",
        "SESSION",
        name="scoring_rule_scope_enum",
        schema="scoring",
        create_type=False,
    )

    score_component_type_enum = postgresql.ENUM(
        "BASE",
        "EXTRA",
        "POWERUP",
        "PENALTY",
        name="score_component_type_enum",
        schema="scoring",
        create_type=False,
    )

    op.create_table(
        "scoring_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("scope", scoring_rule_scope_enum, nullable=False),
        sa.Column(
            "component_type",
            score_component_type_enum,
            nullable=False,
        ),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("evaluator_key", sa.String(length=80), nullable=False),
        sa.Column("priority", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("params_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("bet_context_id", sa.Integer(), nullable=True),
        sa.Column("event_session_id", sa.Integer(), nullable=True),
        sa.Column("bet_score_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("priority >= 0", name="ck_scoring_rules_priority_nonneg"),
        sa.CheckConstraint(
            "(event_session_id IS NULL) OR (bet_context_id IS NOT NULL)",
            name="ck_scoring_rules_session_requires_context",
        ),
        sa.ForeignKeyConstraint(["bet_context_id"], ["betting.bet_contexts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bet_score_id"], ["betting.bet_scores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_session_id"], ["competition.event_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["season_id"], ["competition.seasons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "season_id",
            "scope",
            "code",
            "bet_context_id",
            "event_session_id",
            "bet_score_id",
            name="uq_scoring_rules_scope_code_target",
        ),
        schema="scoring",
    )
    op.create_index("ix_scoring_rules_season_id", "scoring_rules", ["season_id"], unique=False, schema="scoring")
    op.create_index("ix_scoring_rules_scope", "scoring_rules", ["scope"], unique=False, schema="scoring")
    op.create_index(
        "ix_scoring_rules_component_type",
        "scoring_rules",
        ["component_type"],
        unique=False,
        schema="scoring",
    )
    op.create_index(
        "ix_scoring_rules_context_id",
        "scoring_rules",
        ["bet_context_id"],
        unique=False,
        schema="scoring",
    )
    op.create_index(
        "ix_scoring_rules_event_session_id",
        "scoring_rules",
        ["event_session_id"],
        unique=False,
        schema="scoring",
    )
    op.create_index(
        "ix_scoring_rules_bet_score_id",
        "scoring_rules",
        ["bet_score_id"],
        unique=False,
        schema="scoring",
    )


def downgrade() -> None:
    op.drop_index("ix_scoring_rules_bet_score_id", table_name="scoring_rules", schema="scoring")
    op.drop_index("ix_scoring_rules_event_session_id", table_name="scoring_rules", schema="scoring")
    op.drop_index("ix_scoring_rules_context_id", table_name="scoring_rules", schema="scoring")
    op.drop_index("ix_scoring_rules_component_type", table_name="scoring_rules", schema="scoring")
    op.drop_index("ix_scoring_rules_scope", table_name="scoring_rules", schema="scoring")
    op.drop_index("ix_scoring_rules_season_id", table_name="scoring_rules", schema="scoring")
    op.drop_table("scoring_rules", schema="scoring")

    op.execute("DROP TYPE IF EXISTS scoring.scoring_rule_scope_enum")