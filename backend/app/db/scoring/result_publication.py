from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.betting import BetContext
    from app.db.competition import EventSession, TestingEventSession


class ResultPublication(Base):
    __tablename__ = "result_publications"
    __table_args__ = (
        CheckConstraint(
            "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
            name="ck_result_publications_not_both_session_ids",
        ),
        Index(
            "uq_result_publications_ctx_nosession",
            "bet_context_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL AND testing_event_session_id IS NULL"),
        ),
        Index(
            "uq_result_publications_ctx_session",
            "bet_context_id",
            "event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL AND testing_event_session_id IS NULL"),
        ),
        Index(
            "uq_result_publications_ctx_testing_session",
            "bet_context_id",
            "testing_event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL AND testing_event_session_id IS NOT NULL"),
        ),
        Index("ix_result_publications_ctx", "bet_context_id"),
        Index("ix_result_publications_session", "event_session_id"),
        Index("ix_result_publications_testing_session", "testing_event_session_id"),
        Index("ix_result_publications_published_by", "published_by_user_id"),
        Index("ix_result_publications_published_at", "published_at"),
        CheckConstraint(
            "note IS NULL OR length(note) <= 5000",
            name="ck_result_publications_note_len",
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

    published_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    bet_context: Mapped["BetContext"] = relationship(
        "BetContext",
        back_populates="result_publications",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="result_publications",
    )

    testing_event_session: Mapped[Optional["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="result_publications",
    )

    published_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[published_by_user_id],
        back_populates="result_publications_published",
    )
