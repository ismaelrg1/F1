from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, Enum, text, ForeignKey, String, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from typing import TYPE_CHECKING, Optional, Dict, Any

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.scoring import ScoreSession

from app.db.enums import ScoreComponentType

class ScoreSessionComponent(Base):
    __tablename__ = "score_session_components"
    __table_args__ = (
        UniqueConstraint(
            "score_session_id", "component_type", "code",
            name="uq_score_sess_components_sess_type_code",
        ),

        CheckConstraint(
            "points >= 0",
            name="ck_score_sess_components_points_notneg",
        ),

        CheckConstraint("length(code) >= 2", name="ck_score_sess_components_code_minlen"),

        Index("ix_score_sess_components_session_id", "score_session_id"),
        Index("ix_score_sess_components_sess_type", "score_session_id", "component_type"),
        Index("ix_score_sess_components_type", "component_type"),

        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    score_session_id: Mapped[int] = mapped_column(
        ForeignKey("scoring.score_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    component_type: Mapped[ScoreComponentType] = mapped_column(
        Enum(ScoreComponentType, name="score_component_type_enum", schema="scoring", create_type=False),
        nullable=False,
    )

    # Ej: "BET_BASE", "STREAK_5", "FIRST_SUBMIT", "POWERUP_X2", "PENALTY_HALF"
    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    # Más precisión para divisiones/multiplicaciones encadenadas
    points: Mapped[Decimal] = mapped_column(
        Numeric(14, 8),
        nullable=False,
        server_default=text("0"),
    )

    details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    

    score_session: Mapped["ScoreSession"] = relationship(
        "ScoreSession",
        back_populates="score_session_components",
    )

