from __future__ import annotations

from sqlalchemy import Index, String, CheckConstraint, Float, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from typing import TYPE_CHECKING, Optional, List

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetTemplateItem, BetPick, BetException
    from app.db.scoring import OfficialResult, ScoringRule

from app.db.enums import BetValueType


class BetScore(Base):
    __tablename__ = "bet_scores"
    __table_args__ = (
        # code en mayúsculas con _ y números (ej: WINNER, P10, ALO_POS, DNF_DRIVER)
        CheckConstraint(
            "code ~ '^[A-Z0-9_]+$'",
            name="ck_bet_scores_code_format",
        ),

        # base_points >= 0 (si un día quieres permitir negativos como penalización, quítalo)
        CheckConstraint(
            "base_points >= 0",
            name="ck_bet_scores_base_points_nonneg",
        ),

        # code único (normal en un catálogo)
        Index("uq_bet_scores_code", "code", unique=True),

        # para búsquedas rápidas por value_type si filtras por tipo a menudo
        Index("ix_bet_scores_value_type", "value_type"),

        CheckConstraint("length(label) >= 2", name="ck_bet_scores_label_minlen"),

        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    base_points: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    value_type: Mapped[BetValueType] = mapped_column(
        Enum(BetValueType, name="bet_value_type_enum", schema="betting"),
        nullable=False,
    )

    constraints_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    
    template_items: Mapped[List["BetTemplateItem"]] = relationship(
        "BetTemplateItem",
        back_populates="bet_score",
    )


    bet_picks: Mapped[List["BetPick"]] = relationship(
        "BetPick",
        back_populates="bet_score",
    )


    bet_exceptions: Mapped[List["BetException"]] = relationship(
        "BetException",
        back_populates="bet_score",
    )

    official_results: Mapped[list["OfficialResult"]] = relationship(
        'OfficialResult',
        back_populates="bet_score",
    )

    scoring_rules: Mapped[list["ScoringRule"]] = relationship(
        "ScoringRule",
        back_populates="bet_score",
        cascade="all, delete-orphan",
    )
