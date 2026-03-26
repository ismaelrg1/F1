from __future__ import annotations

from sqlalchemy import Index, String, CheckConstraint, Float, ForeignKey, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from typing import TYPE_CHECKING, Optional, Dict, Any

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetScore, BetContext
    from app.db.competition import EventSession


class BetException(Base):
    __tablename__ = "bet_exceptions"
    __table_args__ = (
        # 1) Solo 1 exception por (context, bet_score) cuando NO es por sesión
        Index(
            "uq_bet_exceptions_context_score_nosession",
            "bet_context_id",
            "bet_score_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL"),
        ),

        # 2) Solo 1 exception por (context, session, bet_score) cuando SÍ es por sesión
        Index(
            "uq_bet_exceptions_context_session_score",
            "bet_context_id",
            "event_session_id",
            "bet_score_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL"),
        ),

        # 3) Índices de lookup típicos
        Index("ix_bet_exceptions_context_id", "bet_context_id"),
        Index("ix_bet_exceptions_session_id", "event_session_id"),
        Index("ix_bet_exceptions_score_id", "bet_score_id"),

        # 4) Checks útiles
        CheckConstraint(
            "override_points IS NULL OR override_points >= 0",
            name="ck_bet_exceptions_override_points_nonneg",
        ),

        # 5) no puedes poner override_points, is_disabled y override_constraints_json NULL a la vez 
        CheckConstraint(
            "override_points IS NOT NULL OR is_disabled IS NOT NULL OR override_constraints_json IS NOT NULL",
            name="ck_bet_exceptions_has_effect",
        ),

        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # NULL => override para el evento entero (no sesión)
    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    bet_score_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Si NULL => usa BetScore.base_points
    override_points: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Si NULL => no override (usa enabled normal)
    # Si True => deshabilita esa apuesta en ese contexto/sesión
    is_disabled: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    # NUEVO: para cambiar allowed/min/max/etc en un evento o sesión concreta
    override_constraints_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    note: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )


    bet_score: Mapped["BetScore"] = relationship(
        'BetScore',
        back_populates="bet_exceptions",
    )

    bet_context: Mapped["BetContext"] = relationship(
        'BetContext',
        back_populates="bet_exceptions",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        'EventSession',
        back_populates="bet_exceptions",
    )
