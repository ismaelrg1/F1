from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import DateTime, String, ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season, Circuit, DriverEntry, EventSession
    from app.db.betting import BetContext

from app.db.enums import RaceEventStatus

class RaceEvent(Base):
    __tablename__ = "race_events"
    __table_args__ = {"schema": "competition"}


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    season_id: Mapped[int] = mapped_column(ForeignKey("competition.seasons.id", 
                                            ondelete="RESTRICT"), 
                                            nullable=False,
                                            index=True)
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    circuit_id: Mapped[int] = mapped_column(
        ForeignKey("competition.circuits.id", 
        ondelete="RESTRICT"), 
        nullable=False)
    
    event_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    event_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_event_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_event_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[RaceEventStatus] = mapped_column(
        Enum(RaceEventStatus, name="race_event_status_enum", schema="competition"),
        nullable=False,
        server_default=text("'SCHEDULED'")
        )
    status_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    season: Mapped["Season"] = relationship(
        'Season',
        back_populates="race_events"
    )

    circuit: Mapped["Circuit"] = relationship(
        'Circuit',
        back_populates="race_events"
    )

    driver_entries: Mapped[List["DriverEntry"]] = relationship(
        'DriverEntry',
        back_populates="race_event",
    )

    event_sessions: Mapped[List["EventSession"]] = relationship(
        'EventSession',
        back_populates="race_event",
        cascade="all, delete-orphan",
    )

    bet_context: Mapped[Optional["BetContext"]] = relationship(
        'BetContext',
        back_populates="race_event",
        uselist=False,
    )
