from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import BetScoreRelationType

if TYPE_CHECKING:
    from app.db.betting import BetScore


class BetScoreRelation(Base):
    __tablename__ = "bet_score_relations"
    __table_args__ = (
        CheckConstraint(
            "source_bet_score_id <> target_bet_score_id",
            name="ck_bet_score_relations_no_self_reference",
        ),
        CheckConstraint(
            "note IS NULL OR length(note) <= 500",
            name="ck_bet_score_relations_note_len",
        ),
        Index("ix_bet_score_relations_source_score", "source_bet_score_id"),
        Index("ix_bet_score_relations_target_score", "target_bet_score_id"),
        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    source_bet_score_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="CASCADE"),
        nullable=False,
    )

    target_bet_score_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_scores.id", ondelete="CASCADE"),
        nullable=False,
    )

    relation_type: Mapped[BetScoreRelationType] = mapped_column(
        Enum(BetScoreRelationType, name="bet_score_relation_type_enum", schema="betting"),
        nullable=False,
    )

    config_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    source_bet_score: Mapped["BetScore"] = relationship(
        "BetScore",
        foreign_keys=[source_bet_score_id],
        back_populates="source_relations",
    )

    target_bet_score: Mapped["BetScore"] = relationship(
        "BetScore",
        foreign_keys=[target_bet_score_id],
        back_populates="target_relations",
    )
