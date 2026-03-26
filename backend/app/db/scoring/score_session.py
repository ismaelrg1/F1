from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, DateTime, ForeignKey, func, UniqueConstraint, CheckConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetContext
    from app.db.competition import EventSession
    from app.db.auth import User
    from app.db.scoring import ScoreSessionComponent

class ScoreSession(Base):
    __tablename__ = "score_sessions"
    __table_args__ = (
        # 1 fila por usuario + contexto(GP) + sesión
        UniqueConstraint(
            "user_id", "bet_context_id", "event_session_id",
            name="uq_score_sessions_user_ctx_session",
        ),

        # No negativos (si quieres permitir penalizaciones negativas, quítalos)
        CheckConstraint("base_points >= 0", name="ck_score_sessions_base_points_nonneg"),
        CheckConstraint("total_points >= 0", name="ck_score_sessions_total_points_nonneg"),

        # Para ranking por sesión (filtras por ctx+session y ordenas por total)
        Index(
            "ix_score_sessions_ctx_session_total",
            "bet_context_id", "event_session_id", "total_points",
        ),

        # Lookups por usuario
        Index("ix_score_sessions_user_ctx", "user_id", "bet_context_id"),

        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # El contexto del GP (BetContext.kind = 'GP')
    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    event_session_id: Mapped[int] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="RESTRICT"),
        nullable=False,
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
        'User',
        back_populates="score_sessions",
    )

    bet_context: Mapped["BetContext"] = relationship(
        'BetContext',
        back_populates="score_sessions",
    )

    event_session: Mapped["EventSession"] = relationship(
        'EventSession',
        back_populates="score_sessions",
    )

    score_session_components: Mapped[list["ScoreSessionComponent"]] = relationship(
        "ScoreSessionComponent",
        back_populates="score_session",
        cascade="all, delete-orphan",
    )

