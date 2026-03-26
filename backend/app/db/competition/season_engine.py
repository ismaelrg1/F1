from __future__ import annotations

from sqlalchemy import text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season, Engine


class SeasonEngine(Base):
    __tablename__ = "season_engines"
    __table_args__ = {"schema": "competition"}

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"), 
        primary_key=True
        )
    
    engine_id: Mapped[int] = mapped_column(
        ForeignKey("competition.engines.id", ondelete="RESTRICT"), 
        primary_key=True
        )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    season: Mapped["Season"] = relationship(
        'Season', 
        back_populates="season_engines")
    
    engine: Mapped["Engine"] = relationship(
        'Engine', 
        back_populates="season_engines")
    