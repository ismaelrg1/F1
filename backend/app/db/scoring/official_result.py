from __future__ import annotations

from datetime import datetime
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetContext, BetScore
    from app.db.competition import EventSession, TestingEventSession


class SourceType(str, enum.Enum):
    MANUAL = "MANUAL"
    FASTF1 = "FASTF1"
    OTHER = "OTHER"


class OfficialResult(Base):
    __tablename__ = "official_results"
    __table_args__ = (
        CheckConstraint(
            "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
            name="ck_official_results_not_both_session_ids",
        ),
        Index(
            "uq_official_results_ctx_score_nosession",
            "bet_context_id",
            "bet_score_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL AND testing_event_session_id IS NULL"),
        ),
        Index(
            "uq_official_results_ctx_session_score",
            "bet_context_id",
            "event_session_id",
            "bet_score_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
        ),
        Index(
            "uq_official_results_ctx_testing_session_score",
            "bet_context_id",
            "testing_event_session_id",
            "bet_score_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
        ),
        Index("ix_official_results_ctx", "bet_context_id"),
        Index("ix_official_results_session", "event_session_id"),
        Index("ix_official_results_testing_session", "testing_event_session_id"),
        Index("ix_official_results_score", "bet_score_id"),
        CheckConstraint(
            "value <> ''",
            name="ck_official_results_value_not_empty",
        ),
        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    testing_event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.testing_event_sessions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    bet_score_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="RESTRICT"),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="official_result_source_enum", schema="scoring"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    bet_context: Mapped["BetContext"] = relationship(
        "BetContext",
        back_populates="official_results",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="official_results",
    )

    testing_event_session: Mapped[Optional["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="official_results",
    )

    bet_score: Mapped["BetScore"] = relationship(
        "BetScore",
        back_populates="official_results",
    )
