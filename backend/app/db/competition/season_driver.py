from __future__ import annotations

from sqlalchemy import text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season, Driver

from app.db.enums import SeasonDriverStatus

class SeasonDriver(Base):
    __tablename__ = "season_drivers"
    __table_args__ = {"schema": "competition"}

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"), 
        primary_key=True
        )
    
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("competition.drivers.id", ondelete="RESTRICT"), 
        primary_key=True
        )

    status: Mapped[SeasonDriverStatus] = mapped_column(
        Enum(SeasonDriverStatus, name="season_driver_status_enum", schema="competition"),
        nullable=False,
        server_default=text("'PRIMARY'"),
    )

    season: Mapped["Season"] = relationship(
        'Season', 
        back_populates="season_drivers")
    
    driver: Mapped["Driver"] = relationship(
        'Driver', 
        back_populates="season_drivers")
    