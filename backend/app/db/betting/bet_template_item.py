from __future__ import annotations

from sqlalchemy import ForeignKey, Index, text, Boolean, UniqueConstraint, Integer, CheckConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from typing import TYPE_CHECKING, Any

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetTemplate, BetScore



class BetTemplateItem(Base):
    __tablename__ = "bet_template_items"
    __table_args__ = (
        # Un bet_score solo puede aparecer una vez por template
        UniqueConstraint("template_id", "bet_score_id", name="uq_template_bet_score"),

        # Display_order único dentro del template
        UniqueConstraint("template_id", "display_order", name="uq_template_display_order"),
        CheckConstraint(
            "display_order >= 0",
            name="ck_bet_template_items_display_order_nonneg",
        ),

        Index("ix_template_items_template_id", "template_id"),
        Index("ix_template_items_bet_score_id", "bet_score_id"),

        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    template_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_templates.id", ondelete="CASCADE"),
        nullable=False,
    )

    bet_score_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="RESTRICT"),
        nullable=False,
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    override_points: Mapped[float | None] = mapped_column(
        Numeric,
        nullable=True,
    )

    override_constraints_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )


    bet_template: Mapped["BetTemplate"] = relationship(
        'BetTemplate',
        back_populates="items"
    )

    bet_score: Mapped["BetScore"] = relationship(
        "BetScore",
        back_populates="template_items",
    )


