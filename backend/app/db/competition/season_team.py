from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season, TeamF1


class SeasonTeam(Base):
    __tablename__ = "season_teams"
    __table_args__ = (
        Index("ix_season_teams_team_id", "team_id"),
        {"schema": "competition"},
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"), 
        primary_key=True
        )
    
    team_id: Mapped[int] = mapped_column(
        ForeignKey("competition.teams.id", ondelete="RESTRICT"), 
        primary_key=True
        )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    season: Mapped["Season"] = relationship(
        "app.db.competition.season.Season",
        back_populates="season_teams",
    )

    team: Mapped["TeamF1"] = relationship(
        "app.db.competition.team.TeamF1",
        back_populates="season_teams",
    )
    
