from __future__ import annotations

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season, Driver

from app.db.enums import SeasonDriverStatus

class SeasonDriver(Base):
    __tablename__ = "season_drivers"
    __table_args__ = (
        Index("ix_season_drivers_driver_id", "driver_id"),
        CheckConstraint(
            "driver_number IS NULL OR driver_number > 0",
            name="ck_season_drivers_driver_number_positive",
        ),
        Index(
            "uq_season_drivers_season_driver_number",
            "season_id",
            "driver_number",
            unique=True,
            postgresql_where=text("driver_number IS NOT NULL"),
        ),
        {"schema": "competition"},
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"), 
        primary_key=True
        )
    
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("competition.drivers.id", ondelete="RESTRICT"), 
        primary_key=True
        )

    driver_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
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
    
