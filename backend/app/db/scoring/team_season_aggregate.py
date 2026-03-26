from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    Numeric,
    DateTime,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.social import Team, Group
    from app.db.competition import Season


class TeamSeasonAggregate(Base):
    __tablename__ = "team_season_aggregates"
    __table_args__ = (
        # 1 fila por equipo por temporada por grupo
        Index(
            "uq_team_season_agg_group_team_season",
            "group_id", "team_id", "season_id",
            unique=True,
        ),

        # ranking por temporada
        Index(
            "ix_team_season_agg_rank",
            "group_id", "season_id", "total_points", "computed_at",
        ),

        Index("ix_team_season_agg_team_id", "team_id"),
        Index("ix_team_season_agg_season_id", "season_id"),
        Index("ix_team_season_agg_group_id", "group_id"),

        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("social.teams.id", ondelete="CASCADE"),
        nullable=False,
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"),
        nullable=False,
    )

    total_points: Mapped[Decimal] = mapped_column(
        Numeric(14, 8),
        nullable=False,
        server_default=text("0")
    )

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    group: Mapped["Group"] = relationship(
        "app.db.social.group.Group",
        back_populates="team_season_aggregates",
    )
    team: Mapped["Team"] = relationship(
        "app.db.social.team.Team",
        back_populates="team_season_aggregates",
    )
    season: Mapped["Season"] = relationship(
        "app.db.competition.season.Season",
        back_populates="team_season_aggregates",
    )
