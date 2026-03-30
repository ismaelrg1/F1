from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, DateTime, text, ForeignKey, func, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetContext
    from app.db.auth import User
    from app.db.scoring import ScoreComponent

class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        # 1) Un score por usuario y contexto (evita duplicados)
        UniqueConstraint(
            "user_id", "bet_context_id",
            name="uq_scores_user_context",
        ),

        # (opcional) si NO quieres permitir negativos
        CheckConstraint(
            "base_points >= 0",
            name="ck_scores_base_points_nonneg",
        ),
        CheckConstraint(
            "total_points >= 0",
            name="ck_scores_total_points_nonneg",
        ),

        # 3) Índices típicos de queries
        Index("ix_scores_user_id", "user_id"),
        Index("ix_scores_bet_context_id", "bet_context_id"),

        Index("ix_scores_context_ranking","bet_context_id", "total_points", "computed_at", "user_id"),

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

    base_points: Mapped[Decimal] = mapped_column(
        Numeric(14, 8),
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
        back_populates="scores",
    )

    bet_context: Mapped["BetContext"] = relationship(
        'BetContext',
        back_populates="scores",
    )

    score_components: Mapped[list["ScoreComponent"]] = relationship(
        "ScoreComponent",
        back_populates="score",
        cascade="all, delete-orphan",
    )


