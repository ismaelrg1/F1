from __future__ import annotations

from sqlalchemy import ForeignKey, DateTime, Index, func, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional, List
from datetime import datetime

if TYPE_CHECKING:
    from app.db.competition import EventSession
    from app.db.auth import User
    from app.db.betting import BetContext, BetPick

from app.db.base import Base

class Bet(Base):
    __tablename__ = "bets"
    __table_args__ = ( 
        
        # Un usuario solo puede tener 1 apuesta por contexto y sesión
        # para GP/session
        Index(
            "uq_bets_user_ctx_session_notnull",
            "user_id", "bet_context_id", "event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL"),
        ),
        # para testing/season (sin sesión)
        Index(
            "uq_bets_user_ctx_session_null",
            "user_id", "bet_context_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL"),
        ),

        CheckConstraint(
            "locked_at IS NULL OR submitted_at IS NULL OR locked_at >= submitted_at",
            name="ck_bets_locked_after_submit",
        ),

        Index(
            "ix_bets_ctx_session_ranking",
            "bet_context_id",
            "event_session_id",
            "last_modified_at",
            "id",
            postgresql_where=text("submitted_at IS NOT NULL"),
        ),

        Index(
            "ix_bets_context_ranking",
            "bet_context_id",
            "last_modified_at",
            "id",
            postgresql_where=text("submitted_at IS NOT NULL"),
        ),

        Index("ix_bets_user_context", "user_id", "bet_context_id"),

        {"schema": "betting"}, 
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

    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        'User',
        back_populates="bets",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        'EventSession',
        back_populates="bets"
    )


    bet_context: Mapped["BetContext"] = relationship(
        'BetContext',
        back_populates="bets",
    )

    bet_picks: Mapped[List["BetPick"]] = relationship(
        "BetPick",
        back_populates="bet",
        cascade="all, delete-orphan",
    )




'''
🏁 1️⃣ Ranking por SESSION (GP sesión)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY b.last_modified_at ASC, b.id ASC
    ) AS ranking,
    u.username,
    b.event_session_id AS session_id,
    b.last_modified_at AS tiempo_submitted
FROM betting.bets b
JOIN auth.users u ON u.id = b.user_id
JOIN competition.event_sessions s ON s.id = b.event_session_id
WHERE b.event_session_id = :session_id
  AND b.submitted_at IS NOT NULL
ORDER BY ranking;

🧪 2️⃣ Ranking para TESTING (por bet_context_id)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY b.last_modified_at ASC, b.id ASC
    ) AS ranking,
    u.username,
    b.bet_context_id AS context_id,
    b.last_modified_at AS tiempo_submitted
FROM betting.bets b
JOIN auth.users u ON u.id = b.user_id
WHERE b.bet_context_id = :testing_context_id
  AND b.submitted_at IS NOT NULL
ORDER BY ranking;

🏆 3️⃣ Ranking para TEMPORADA (por bet_context_id)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY b.last_modified_at ASC, b.id ASC
    ) AS ranking,
    u.username,
    b.bet_context_id AS context_id,
    b.last_modified_at AS tiempo_submitted
FROM betting.bets b
JOIN auth.users u ON u.id = b.user_id
WHERE b.bet_context_id = :season_context_id
  AND b.submitted_at IS NOT NULL
ORDER BY ranking;

'''



