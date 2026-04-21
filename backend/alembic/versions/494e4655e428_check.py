"""add testing session support to scoring

Revision ID: 494e4655e428
Revises: 4956d872e40c
Create Date: 2026-04-21 09:35:07.232398
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "494e4655e428"
down_revision = "4956d872e40c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "uq_official_results_ctx_score_nosession",
        table_name="official_results",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
    op.drop_index(
        "uq_official_results_ctx_session_score",
        table_name="official_results",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "uq_result_publications_ctx_nosession",
        table_name="result_publications",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
    op.drop_index(
        "uq_result_publications_ctx_session",
        table_name="result_publications",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "ix_score_sessions_ctx_session_total",
        table_name="score_sessions",
        schema="scoring",
    )
    op.drop_constraint(
        "uq_score_sessions_user_ctx_session",
        "score_sessions",
        schema="scoring",
        type_="unique",
    )

    op.add_column(
        "official_results",
        sa.Column("testing_event_session_id", sa.Integer(), nullable=True),
        schema="scoring",
    )
    op.add_column(
        "result_publications",
        sa.Column("testing_event_session_id", sa.Integer(), nullable=True),
        schema="scoring",
    )
    op.add_column(
        "score_sessions",
        sa.Column("testing_event_session_id", sa.Integer(), nullable=True),
        schema="scoring",
    )
    op.alter_column(
        "score_sessions",
        "event_session_id",
        existing_type=sa.Integer(),
        nullable=True,
        schema="scoring",
    )

    op.create_foreign_key(
        "fk_official_results_testing_event_session_id",
        "official_results",
        "testing_event_sessions",
        ["testing_event_session_id"],
        ["id"],
        source_schema="scoring",
        referent_schema="competition",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_result_publications_testing_event_session_id",
        "result_publications",
        "testing_event_sessions",
        ["testing_event_session_id"],
        ["id"],
        source_schema="scoring",
        referent_schema="competition",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_score_sessions_testing_event_session_id",
        "score_sessions",
        "testing_event_sessions",
        ["testing_event_session_id"],
        ["id"],
        source_schema="scoring",
        referent_schema="competition",
        ondelete="RESTRICT",
    )

    op.create_check_constraint(
        "ck_official_results_not_both_session_ids",
        "official_results",
        "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
        schema="scoring",
    )
    op.create_check_constraint(
        "ck_result_publications_not_both_session_ids",
        "result_publications",
        "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
        schema="scoring",
    )
    op.create_check_constraint(
        "ck_score_sessions_not_both_session_ids",
        "score_sessions",
        "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
        schema="scoring",
    )
    op.create_check_constraint(
        "ck_score_sessions_requires_session_id",
        "score_sessions",
        "event_session_id IS NOT NULL OR testing_event_session_id IS NOT NULL",
        schema="scoring",
    )

    op.create_index(
        "uq_official_results_ctx_score_nosession",
        "official_results",
        ["bet_context_id", "bet_score_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NULL"),
    )
    op.create_index(
        "uq_official_results_ctx_session_score",
        "official_results",
        ["bet_context_id", "event_session_id", "bet_score_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
    )
    op.create_index(
        "uq_official_results_ctx_testing_session_score",
        "official_results",
        ["bet_context_id", "testing_event_session_id", "bet_score_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
    )
    op.create_index(
        "ix_official_results_testing_session",
        "official_results",
        ["testing_event_session_id"],
        unique=False,
        schema="scoring",
    )

    op.create_index(
        "uq_result_publications_ctx_nosession",
        "result_publications",
        ["bet_context_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NULL"),
    )
    op.create_index(
        "uq_result_publications_ctx_session",
        "result_publications",
        ["bet_context_id", "event_session_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
    )
    op.create_index(
        "uq_result_publications_ctx_testing_session",
        "result_publications",
        ["bet_context_id", "testing_event_session_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
    )
    op.create_index(
        "ix_result_publications_testing_session",
        "result_publications",
        ["testing_event_session_id"],
        unique=False,
        schema="scoring",
    )

    op.create_index(
        "uq_score_sessions_user_ctx_session",
        "score_sessions",
        ["user_id", "bet_context_id", "event_session_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
    )
    op.create_index(
        "uq_score_sessions_user_ctx_testing_session",
        "score_sessions",
        ["user_id", "bet_context_id", "testing_event_session_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
    )
    op.create_index(
        "ix_score_sessions_ctx_session_total",
        "score_sessions",
        ["bet_context_id", "event_session_id", "total_points"],
        unique=False,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.create_index(
        "ix_score_sessions_ctx_testing_session_total",
        "score_sessions",
        ["bet_context_id", "testing_event_session_id", "total_points"],
        unique=False,
        schema="scoring",
        postgresql_where=sa.text("testing_event_session_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_score_sessions_ctx_testing_session_total",
        table_name="score_sessions",
        schema="scoring",
        postgresql_where=sa.text("testing_event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "ix_score_sessions_ctx_session_total",
        table_name="score_sessions",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "uq_score_sessions_user_ctx_testing_session",
        table_name="score_sessions",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "uq_score_sessions_user_ctx_session",
        table_name="score_sessions",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
    )

    op.drop_index(
        "ix_result_publications_testing_session",
        table_name="result_publications",
        schema="scoring",
    )
    op.drop_index(
        "uq_result_publications_ctx_testing_session",
        table_name="result_publications",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "uq_result_publications_ctx_session",
        table_name="result_publications",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
    )
    op.drop_index(
        "uq_result_publications_ctx_nosession",
        table_name="result_publications",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NULL"),
    )

    op.drop_index(
        "ix_official_results_testing_session",
        table_name="official_results",
        schema="scoring",
    )
    op.drop_index(
        "uq_official_results_ctx_testing_session_score",
        table_name="official_results",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
    )
    op.drop_index(
        "uq_official_results_ctx_session_score",
        table_name="official_results",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
    )
    op.drop_index(
        "uq_official_results_ctx_score_nosession",
        table_name="official_results",
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL AND testing_event_session_id IS NULL"),
    )

    op.drop_constraint(
        "ck_score_sessions_requires_session_id",
        "score_sessions",
        schema="scoring",
        type_="check",
    )
    op.drop_constraint(
        "ck_score_sessions_not_both_session_ids",
        "score_sessions",
        schema="scoring",
        type_="check",
    )
    op.drop_constraint(
        "ck_result_publications_not_both_session_ids",
        "result_publications",
        schema="scoring",
        type_="check",
    )
    op.drop_constraint(
        "ck_official_results_not_both_session_ids",
        "official_results",
        schema="scoring",
        type_="check",
    )

    op.drop_constraint(
        "fk_score_sessions_testing_event_session_id",
        "score_sessions",
        schema="scoring",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_result_publications_testing_event_session_id",
        "result_publications",
        schema="scoring",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_official_results_testing_event_session_id",
        "official_results",
        schema="scoring",
        type_="foreignkey",
    )

    op.execute(
        "DELETE FROM scoring.score_sessions "
        "WHERE event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
    )
    op.execute(
        "DELETE FROM scoring.result_publications "
        "WHERE event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
    )
    op.execute(
        "DELETE FROM scoring.official_results "
        "WHERE event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
    )

    op.drop_column("score_sessions", "testing_event_session_id", schema="scoring")
    op.drop_column("result_publications", "testing_event_session_id", schema="scoring")
    op.drop_column("official_results", "testing_event_session_id", schema="scoring")

    op.alter_column(
        "score_sessions",
        "event_session_id",
        existing_type=sa.Integer(),
        nullable=False,
        schema="scoring",
    )

    op.create_unique_constraint(
        "uq_score_sessions_user_ctx_session",
        "score_sessions",
        ["user_id", "bet_context_id", "event_session_id"],
        schema="scoring",
    )
    op.create_index(
        "ix_score_sessions_ctx_session_total",
        "score_sessions",
        ["bet_context_id", "event_session_id", "total_points"],
        unique=False,
        schema="scoring",
    )
    op.create_index(
        "uq_result_publications_ctx_session",
        "result_publications",
        ["bet_context_id", "event_session_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.create_index(
        "uq_result_publications_ctx_nosession",
        "result_publications",
        ["bet_context_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
    op.create_index(
        "uq_official_results_ctx_session_score",
        "official_results",
        ["bet_context_id", "event_session_id", "bet_score_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NOT NULL"),
    )
    op.create_index(
        "uq_official_results_ctx_score_nosession",
        "official_results",
        ["bet_context_id", "bet_score_id"],
        unique=True,
        schema="scoring",
        postgresql_where=sa.text("event_session_id IS NULL"),
    )
