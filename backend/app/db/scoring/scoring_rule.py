from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import ScoreComponentType, ScoringRuleScope

if TYPE_CHECKING:
    from app.db.betting import BetContext, BetScore
    from app.db.competition import EventSession, Season


class ScoringRule(Base):
    __tablename__ = "scoring_rules"
    __table_args__ = (
        CheckConstraint(
            "priority >= 0",
            name="ck_scoring_rules_priority_nonneg",
        ),
        CheckConstraint(
            "(event_session_id IS NULL) OR (bet_context_id IS NOT NULL)",
            name="ck_scoring_rules_session_requires_context",
        ),
        CheckConstraint(
            "("
            " (scope = 'GLOBAL' AND bet_context_id IS NULL AND event_session_id IS NULL AND bet_score_id IS NULL) OR "
            " (scope = 'BET_SCORE' AND bet_score_id IS NOT NULL AND bet_context_id IS NULL AND event_session_id IS NULL) OR "
            " (scope = 'CONTEXT' AND bet_context_id IS NOT NULL AND event_session_id IS NULL AND bet_score_id IS NULL) OR "
            " (scope = 'SESSION' AND bet_context_id IS NOT NULL AND event_session_id IS NOT NULL AND bet_score_id IS NULL) "
            ")",
            name="ck_scoring_rules_scope_targets",
        ),
        CheckConstraint("length(code) >= 2", name="ck_scoring_rules_code_minlen"),
        CheckConstraint(
            "length(evaluator_key) >= 2",
            name="ck_scoring_rules_evaluator_key_minlen",
        ),
        Index(
            "uq_scoring_rules_global",
            "season_id",
            "code",
            unique=True,
            postgresql_where=text(
                "scope = 'GLOBAL' AND bet_context_id IS NULL AND event_session_id IS NULL AND bet_score_id IS NULL"
            ),
        ),
        Index(
            "uq_scoring_rules_bet_score",
            "season_id",
            "code",
            "bet_score_id",
            unique=True,
            postgresql_where=text(
                "scope = 'BET_SCORE' AND bet_score_id IS NOT NULL AND bet_context_id IS NULL AND event_session_id IS NULL"
            ),
        ),
        Index(
            "uq_scoring_rules_context",
            "season_id",
            "code",
            "bet_context_id",
            unique=True,
            postgresql_where=text(
                "scope = 'CONTEXT' AND bet_context_id IS NOT NULL AND event_session_id IS NULL AND bet_score_id IS NULL"
            ),
        ),
        Index(
            "uq_scoring_rules_session",
            "season_id",
            "code",
            "bet_context_id",
            "event_session_id",
            unique=True,
            postgresql_where=text(
                "scope = 'SESSION' AND bet_context_id IS NOT NULL AND event_session_id IS NOT NULL AND bet_score_id IS NULL"
            ),
        ),
        Index("ix_scoring_rules_season_id", "season_id"),
        Index("ix_scoring_rules_scope", "scope"),
        Index("ix_scoring_rules_component_type", "component_type"),
        Index("ix_scoring_rules_context_id", "bet_context_id"),
        Index("ix_scoring_rules_event_session_id", "event_session_id"),
        Index("ix_scoring_rules_bet_score_id", "bet_score_id"),
        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="CASCADE"),
        nullable=False,
    )

    scope: Mapped[ScoringRuleScope] = mapped_column(
        Enum(ScoringRuleScope, name="scoring_rule_scope_enum", schema="scoring"),
        nullable=False,
    )

    component_type: Mapped[ScoreComponentType] = mapped_column(
        Enum(ScoreComponentType, name="score_component_type_enum", schema="scoring", create_type=False),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    evaluator_key: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("100"),
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    params_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    bet_context_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=True,
    )

    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    bet_score_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="CASCADE"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="scoring_rules",
    )

    bet_context: Mapped[Optional["BetContext"]] = relationship(
        "BetContext",
        back_populates="scoring_rules",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="scoring_rules",
    )

    bet_score: Mapped[Optional["BetScore"]] = relationship(
        "BetScore",
        back_populates="scoring_rules",
    )
