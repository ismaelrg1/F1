from __future__ import annotations

from sqlalchemy import ForeignKey, DateTime, Index, Integer, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional
from datetime import datetime

if TYPE_CHECKING:
    from app.db.betting import Bet

from app.db.base import Base

class BetSubmissionRevision(Base):
    __tablename__ = "bet_submission_revisions"
    __table_args__ = (
        UniqueConstraint(
            "bet_id",
            "revision_number",
            name="uq_bet_submission_revisions_bet_revision",
        ),
        Index(
            "ix_bet_submission_revisions_bet_id",
            "bet_id",
        ),
        CheckConstraint(
            "revision_number >= 1",
            name="ck_bet_submission_revisions_revision_positive",
        ),
        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    bet_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bets.id", ondelete="CASCADE"),
        nullable=False,
    )

    revision_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    bet: Mapped["Bet"] = relationship(
        "Bet",
        back_populates="submission_revisions",
    )