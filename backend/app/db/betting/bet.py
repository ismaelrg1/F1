from __future__ import annotations

from sqlalchemy import ForeignKey, DateTime, Index, func, CheckConstraint, text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional, List
from datetime import datetime

if TYPE_CHECKING:
    from app.db.competition import EventSession, TestingEventSession
    from app.db.auth import User
    from app.db.betting import BetContext, BetPick, BetSubmissionRevision

from app.db.base import Base

class Bet(Base):
    __tablename__ = "bets"
    __table_args__ = (
        # Un usuario solo puede tener 1 apuesta por contexto y sesión GP.
        Index(
            "uq_bets_user_ctx_gp_session",
            "user_id",
            "bet_context_id",
            "event_session_id",
            unique=True,
            postgresql_where=text(
                "event_session_id IS NOT NULL AND testing_event_session_id IS NULL"
            ),
        ),

        # Un usuario solo puede tener 1 apuesta por contexto y sesión de testing.
        Index(
            "uq_bets_user_ctx_testing_session",
            "user_id",
            "bet_context_id",
            "testing_event_session_id",
            unique=True,
            postgresql_where=text(
                "testing_event_session_id IS NOT NULL AND event_session_id IS NULL"
            ),
        ),

        # Un usuario solo puede tener 1 apuesta global por contexto sin sesión.
        # Sirve para season, testing global o preguntas globales de GP.
        Index(
            "uq_bets_user_ctx_no_session",
            "user_id",
            "bet_context_id",
            unique=True,
            postgresql_where=text(
                "event_session_id IS NULL AND testing_event_session_id IS NULL"
            ),
        ),

        # Nunca puede apuntar a una sesión GP y a una sesión de testing a la vez.
        CheckConstraint(
            "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
            name="ck_bets_not_both_session_ids",
        ),

        # Si existe locked_at y submitted_at, locked_at debe ser posterior o igual.
        CheckConstraint(
            "locked_at IS NULL OR submitted_at IS NULL OR locked_at >= submitted_at",
            name="ck_bets_locked_after_submit",
        ),

        # Índice para ranking/envío de apuestas por sesión GP.
        Index(
            "ix_bets_ctx_gp_session_ranking",
            "bet_context_id",
            "event_session_id",
            "last_modified_at",
            "id",
            postgresql_where=text(
                "submitted_at IS NOT NULL AND event_session_id IS NOT NULL"
            ),
        ),

        # Índice para ranking/envío de apuestas por sesión de testing.
        Index(
            "ix_bets_ctx_testing_session_ranking",
            "bet_context_id",
            "testing_event_session_id",
            "last_modified_at",
            "id",
            postgresql_where=text(
                "submitted_at IS NOT NULL AND testing_event_session_id IS NOT NULL"
            ),
        ),

        # Índice para apuestas globales sin sesión.
        Index(
            "ix_bets_context_ranking",
            "bet_context_id",
            "last_modified_at",
            "id",
            postgresql_where=text(
                "submitted_at IS NOT NULL "
                "AND event_session_id IS NULL "
                "AND testing_event_session_id IS NULL"
            ),
        ),

        # Lookup habitual por usuario + contexto.
        Index("ix_bets_user_context", "user_id", "bet_context_id"),

        Index(
            "ix_bets_context_submit_order",
            "bet_context_id",
            "submit_order_int",
            "id",
            postgresql_where=text(
                "submitted_at IS NOT NULL "
                "AND event_session_id IS NULL "
                "AND testing_event_session_id IS NULL "
                "AND submit_order_int IS NOT NULL"
            ),
        ),

        Index(
            "ix_bets_gp_session_submit_order",
            "bet_context_id",
            "event_session_id",
            "submit_order_int",
            "id",
            postgresql_where=text(
                "submitted_at IS NOT NULL "
                "AND event_session_id IS NOT NULL "
                "AND submit_order_int IS NOT NULL"
            ),
        ),

        Index(
            "ix_bets_testing_session_submit_order",
            "bet_context_id",
            "testing_event_session_id",
            "submit_order_int",
            "id",
            postgresql_where=text(
                "submitted_at IS NOT NULL "
                "AND testing_event_session_id IS NOT NULL "
                "AND submit_order_int IS NOT NULL"
            ),
        ),

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

    testing_event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.testing_event_sessions.id", ondelete="RESTRICT"),
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

    submit_order_int: Mapped[Optional[int]] = mapped_column(
        Integer,
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

    testing_event_session: Mapped[Optional["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="bets",
    )

    submission_revisions: Mapped[List["BetSubmissionRevision"]] = relationship(
        "BetSubmissionRevision",
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



