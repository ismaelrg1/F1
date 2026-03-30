from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy import Numeric, DateTime, text, ForeignKey, func, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.competition import Season
    from app.db.social import Group


class ScoreSeasonAggregate(Base):
    __tablename__ = "score_season_aggregates"
    __table_args__ = (
        Index(
            "uq_score_season_agg_group_user_season",
            "group_id", "user_id", "season_id",
            unique=True,
        ),

        Index(
            "ix_score_season_agg_group_season_rank",
            "group_id", "season_id", "total_points", "computed_at",
        ),

        CheckConstraint(
            "total_points >= 0",
            name="ck_score_season_agg_points_notneg",
        ),

        Index("ix_score_season_agg_user_id", "user_id"),
        Index("ix_score_season_agg_season_id", "season_id"),
        Index("ix_score_season_agg_group_id", "group_id"),
        Index("ix_score_season_agg_group_user", "group_id", "user_id"),

        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"),
        nullable=False,
    )

    total_points: Mapped[Decimal] = mapped_column(
        Numeric(14, 8),
        nullable=False,
        server_default=text("0"),
    )

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="score_season_aggregates",
    )


    user: Mapped["User"] = relationship(
        'User',
        back_populates="score_season_aggregates",
    )

    season: Mapped["Season"] = relationship(
        'Season',
        back_populates="score_season_aggregates",
    )


