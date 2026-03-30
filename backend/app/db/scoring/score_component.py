from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, Enum, text, ForeignKey, String, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from typing import TYPE_CHECKING, Optional, Dict, Any

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.scoring import Score

from app.db.enums import ScoreComponentType

class ScoreComponent(Base):
    __tablename__ = "score_components"
    __table_args__ = (
        # Evita duplicar el mismo "concepto" dentro del mismo score
        UniqueConstraint(
            "score_id", "component_type", "code",
            name="uq_score_components_score_type_code",
        ),

        # Puntos razonables (puede ser negativo si una penalización resta)
        # Si quieres prohibir negativos, cambia a "points >= 0"
        CheckConstraint(
            "points >= 0",
            name="ck_score_components_points_notneg",
        ),

        CheckConstraint("length(code) >= 2", name="ck_score_components_code_minlen"),

        # Para queries típicas: sumar componentes por score, filtrar por tipo
        Index("ix_score_components_score_id", "score_id"),
        Index("ix_score_components_score_type", "score_id", "component_type"),
        Index("ix_score_components_type", "component_type"),

        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    score_id: Mapped[int] = mapped_column(
        ForeignKey("scoring.scores.id", ondelete="CASCADE"),
        nullable=False,
    )

    component_type: Mapped[ScoreComponentType] = mapped_column(
        Enum(ScoreComponentType, name="score_component_type_enum", schema="scoring"),
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

    # Datos libres (ej: {"bet_score_id": 12, "multiplier": 2, ...})
    details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    

    score: Mapped["Score"] = relationship(
        'Score',
        back_populates="score_components",
    )

