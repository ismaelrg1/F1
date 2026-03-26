from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import func, Enum, ForeignKey, String, text, CheckConstraint, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship


from typing import TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import EventSession
    from app.db.betting import BetContext, BetScore


class SourceType(str, enum.Enum):
    MANUAL = "MANUAL"           # origen manual
    FASTF1 = "FASTF1"           # origen F1
    OTHER  = "OTHER"            # origen otro


class OfficialResult(Base):
    __tablename__ = "official_results"
    __table_args__ = (
        # 1) Solo 1 resultado por (contexto + bet_score) cuando NO es por sesión
        Index(
            "uq_official_results_ctx_score_nosession",
            "bet_context_id",
            "bet_score_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL"),
        ),

        # 2) Solo 1 resultado por (contexto + sesión + bet_score) cuando SÍ es por sesión
        Index(
            "uq_official_results_ctx_session_score",
            "bet_context_id",
            "event_session_id",
            "bet_score_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL"),
        ),

        # 3) Índices típicos de lookup
        Index("ix_official_results_ctx", "bet_context_id"),
        Index("ix_official_results_session", "event_session_id"),
        Index("ix_official_results_score", "bet_score_id"),

        # 4) Checks útiles
        CheckConstraint(
            "value <> ''",
            name="ck_official_results_value_not_empty",
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

    bet_score_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="RESTRICT"),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="official_result_source_enum", schema="scoring"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    bet_context: Mapped["BetContext"] = relationship(
        'BetContext',
        back_populates="official_results",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        'EventSession',
        back_populates="official_results",
    )

    bet_score: Mapped["BetScore"] = relationship(
        'BetScore',
        back_populates="official_results",
    )

