"""add missing bet score relations table

Revision ID: 9b2d4c6f8a10
Revises: e4f9a2b7c6d1
Create Date: 2026-08-06 21:15:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "9b2d4c6f8a10"
down_revision = "e4f9a2b7c6d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("bet_score_relations", schema="betting"):
        return

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = 'bet_score_relation_type_enum'
                  AND n.nspname = 'betting'
            ) THEN
                CREATE TYPE betting.bet_score_relation_type_enum AS ENUM (
                    'DISTINCT',
                    'IMPLIES_VALUE',
                    'MATCHES_POSITION',
                    'MUTUALLY_EXCLUSIVE'
                );
            END IF;
        END
        $$;
        """
    )
    op.create_table(
        "bet_score_relations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_bet_score_id", sa.Integer(), nullable=False),
        sa.Column("target_bet_score_id", sa.Integer(), nullable=False),
        sa.Column(
            "relation_type",
            postgresql.ENUM(
                "DISTINCT",
                "IMPLIES_VALUE",
                "MATCHES_POSITION",
                "MUTUALLY_EXCLUSIVE",
                name="bet_score_relation_type_enum",
                schema="betting",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.CheckConstraint(
            "source_bet_score_id <> target_bet_score_id",
            name="ck_bet_score_relations_no_self_reference",
        ),
        sa.CheckConstraint(
            "note IS NULL OR length(note) <= 500",
            name="ck_bet_score_relations_note_len",
        ),
        sa.ForeignKeyConstraint(
            ["source_bet_score_id"],
            ["betting.bet_scores.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_bet_score_id"],
            ["betting.bet_scores.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="betting",
    )
    op.create_index(
        "ix_bet_score_relations_source_score",
        "bet_score_relations",
        ["source_bet_score_id"],
        unique=False,
        schema="betting",
    )
    op.create_index(
        "ix_bet_score_relations_target_score",
        "bet_score_relations",
        ["target_bet_score_id"],
        unique=False,
        schema="betting",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_bet_score_relations_target_score",
        table_name="bet_score_relations",
        schema="betting",
    )
    op.drop_index(
        "ix_bet_score_relations_source_score",
        table_name="bet_score_relations",
        schema="betting",
    )
    op.drop_table("bet_score_relations", schema="betting")
    op.execute("DROP TYPE IF EXISTS betting.bet_score_relation_type_enum")
