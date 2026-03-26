from __future__ import annotations

from sqlalchemy import ForeignKey, DateTime, Index, UniqueConstraint, CheckConstraint, text, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional
from datetime import datetime

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.betting import Bet, BetScore

from app.db.base import Base

class BetPick(Base):
    __tablename__ = "bet_picks"
    __table_args__ = (
        UniqueConstraint("bet_id", "bet_score_id", name="uq_bet_picks_bet_score"),

        Index("ix_bet_picks_bet_id", "bet_id"),
        Index("ix_bet_picks_score_id", "bet_score_id"),
        Index("ix_bet_picks_invalidated_by", "invalidated_by_user_id"),

        # 🔎 Muy útil si haces moderación/listados de inválidas
        Index(
            "ix_bet_picks_invalid",
            "bet_id",
            postgresql_where=text("is_invalid = true"),
        ),

        # ✅ coherencia de invalidación
        CheckConstraint(
            "(is_invalid = false AND invalid_reason IS NULL AND invalidated_at IS NULL AND invalidated_by_user_id IS NULL) "
            "OR (is_invalid = true AND invalidated_at IS NOT NULL)",
            name="ck_bet_picks_invalid_consistency",
        ),
        CheckConstraint(
            "invalidated_by_user_id IS NULL OR invalidated_at IS NOT NULL",
            name="ck_bet_picks_invalid_by_requires_time",
        ),

        {"schema": "betting"},
    )
    

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    bet_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bets.id", ondelete="CASCADE"),
        nullable=False,
    )

    bet_score_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="CASCADE"),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_invalid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    invalid_reason: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
    )

    invalidated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    invalidated_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True
    )



    invalidated_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[invalidated_by_user_id],
        back_populates="bet_picks_invalidated",
    )

    bet: Mapped["Bet"] = relationship(
        'Bet',
        back_populates="bet_picks"
    )

    bet_score: Mapped["BetScore"] = relationship(
        'BetScore',
        back_populates="bet_picks",
    )


