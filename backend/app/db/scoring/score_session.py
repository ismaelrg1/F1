from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.betting import BetContext
    from app.db.competition import EventSession, TestingEventSession
    from app.db.scoring import ScoreSessionComponent


class ScoreSession(Base):
    __tablename__ = "score_sessions"
    __table_args__ = (
        CheckConstraint(
            "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
            name="ck_score_sessions_not_both_session_ids",
        ),
        CheckConstraint(
            "event_session_id IS NOT NULL OR testing_event_session_id IS NOT NULL",
            name="ck_score_sessions_requires_session_id",
        ),
        CheckConstraint("base_points >= 0", name="ck_score_sessions_base_points_nonneg"),
        CheckConstraint("total_points >= 0", name="ck_score_sessions_total_points_nonneg"),
        Index(
            "uq_score_sessions_user_ctx_session",
            "user_id",
            "bet_context_id",
            "event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
        ),
        Index(
            "uq_score_sessions_user_ctx_testing_session",
            "user_id",
            "bet_context_id",
            "testing_event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
        ),
        Index(
            "ix_score_sessions_ctx_session_total",
            "bet_context_id",
            "event_session_id",
            "total_points",
            postgresql_where=text("event_session_id IS NOT NULL"),
        ),
        Index(
            "ix_score_sessions_ctx_testing_session_total",
            "bet_context_id",
            "testing_event_session_id",
            "total_points",
            postgresql_where=text("testing_event_session_id IS NOT NULL"),
        ),
        Index("ix_score_sessions_user_ctx", "user_id", "bet_context_id", "computed_at"),
        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="RESTRICT"),
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

    base_points: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        server_default=text("0"),
    )

    total_points: Mapped[Decimal] = mapped_column(
        Numeric(14, 8),
        nullable=False,
        server_default=text("0"),
    )

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="score_sessions",
    )

    bet_context: Mapped["BetContext"] = relationship(
        "BetContext",
        back_populates="score_sessions",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="score_sessions",
    )

    testing_event_session: Mapped[Optional["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="score_sessions",
    )

    score_session_components: Mapped[list["ScoreSessionComponent"]] = relationship(
        "ScoreSessionComponent",
        back_populates="score_session",
        cascade="all, delete-orphan",
    )
