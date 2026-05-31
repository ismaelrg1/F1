from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetContext
    from app.db.competition import EventSession, TestingEventSession
    from app.db.powerups import PowerUp


class PowerUpRestriction(Base):
    __tablename__ = "powerup_restrictions"
    __table_args__ = (
        Index(
            "uq_powerup_restrictions_ctx_nosession",
            "powerup_id",
            "bet_context_id",
            unique=True,
            postgresql_where=text(
                "event_session_id IS NULL AND testing_event_session_id IS NULL"
            ),
        ),
        Index(
            "uq_powerup_restrictions_ctx_event_session",
            "powerup_id",
            "bet_context_id",
            "event_session_id",
            unique=True,
            postgresql_where=text(
                "event_session_id IS NOT NULL AND testing_event_session_id IS NULL"
            ),
        ),
        Index(
            "uq_powerup_restrictions_ctx_testing_session",
            "powerup_id",
            "bet_context_id",
            "testing_event_session_id",
            unique=True,
            postgresql_where=text(
                "event_session_id IS NULL AND testing_event_session_id IS NOT NULL"
            ),
        ),
        Index("ix_powerup_restrictions_powerup_id", "powerup_id"),
        Index("ix_powerup_restrictions_ctx_id", "bet_context_id"),
        Index("ix_powerup_restrictions_session_id", "event_session_id"),
        Index("ix_powerup_restrictions_testing_session_id", "testing_event_session_id"),
        Index("ix_powerup_restrictions_is_disabled", "is_disabled"),
        CheckConstraint(
            "note IS NULL OR length(note) <= 5000",
            name="ck_powerup_restrictions_note_len",
        ),
        CheckConstraint(
            "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
            name="ck_powerup_restrictions_single_session_scope",
        ),
        {"schema": "powerups"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    powerup_id: Mapped[int] = mapped_column(
        ForeignKey("powerups.powerups.id", ondelete="CASCADE"),
        nullable=False,
    )

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # NULL => aplica al contexto completo
    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    # NULL => aplica al contexto completo de testing
    testing_event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.testing_event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    is_disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    powerup: Mapped["PowerUp"] = relationship(
        "PowerUp",
        back_populates="restrictions",
    )

    bet_context: Mapped["BetContext"] = relationship(
        "BetContext",
        back_populates="powerup_restrictions",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="powerup_restrictions",
    )

    testing_event_session: Mapped[Optional["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="powerup_restrictions",
    )
