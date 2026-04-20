from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import BetResultsVisibilityMode

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.betting import BetContext
    from app.db.competition import EventSession, TestingEventSession


class BetResultsVisibilityPolicy(Base):
    __tablename__ = "bet_results_visibility_policies"
    __table_args__ = (
        CheckConstraint(
            "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
            name="ck_bet_results_visibility_not_both_session_ids",
        ),
        CheckConstraint(
            "starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at",
            name="ck_bet_results_visibility_window_order",
        ),
        Index(
            "ix_bet_results_visibility_scope",
            "bet_context_id",
            "event_session_id",
            "testing_event_session_id",
        ),
        Index(
            "ix_bet_results_visibility_window",
            "starts_at",
            "ends_at",
        ),
        Index(
            "uq_bet_results_visibility_context_event_scope",
            "bet_context_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL AND testing_event_session_id IS NULL")
        ),
        Index(
            "uq_bet_results_visibility_context_race_session",
            "bet_context_id",
            "event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL")
        ),
        Index(
            "uq_bet_results_visibility_context_testing_session",
            "bet_context_id",
            "testing_event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL")
        ),
        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    testing_event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.testing_event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    visibility_mode: Mapped[BetResultsVisibilityMode] = mapped_column(
        Enum(
            BetResultsVisibilityMode,
            name="bet_results_visibility_mode_enum",
            schema="betting",
        ),
        nullable=False,
    )

    starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    bet_context: Mapped["BetContext"] = relationship(
        "BetContext",
        back_populates="results_visibility_policies",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="bet_results_visibility_policies",
    )

    testing_event_session: Mapped[Optional["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="bet_results_visibility_policies",
    )

    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_bet_results_visibility_policies",
    )