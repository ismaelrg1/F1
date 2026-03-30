from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import DateTime, String, ForeignKey, Enum, Index, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season, Circuit, TestingEventSession
    from app.db.betting import BetContext

from app.db.enums import TestingEventStatus

class TestingEvent(Base):
    __tablename__ = "testing_events"
    __table_args__ = (
        Index("ix_testing_events_public_id", "public_id"),
        {"schema": "competition"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4,
    )

    season_id: Mapped[int] = mapped_column(ForeignKey("competition.seasons.id", 
                                            ondelete="RESTRICT"), 
                                            nullable=False,
                                            index=True)
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    circuit_id: Mapped[int] = mapped_column(ForeignKey("competition.circuits.id", 
                                            ondelete="RESTRICT"), 
                                            nullable=False)
    
    event_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    event_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_event_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_event_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[TestingEventStatus] = mapped_column(
                                        Enum(TestingEventStatus, name="testing_event_status_enum", schema="competition"),
                                        nullable=False,
                                        server_default=text("'SCHEDULED'")
                                        )
    status_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    season: Mapped["Season"] = relationship(
        'Season',
        back_populates="testing_events"
    )

    circuit: Mapped["Circuit"] = relationship(
        'Circuit',
        back_populates="testing_events"

    )

    sessions: Mapped[List["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="testing_event",
        cascade="all, delete-orphan",
    )

    bet_context: Mapped[Optional["BetContext"]] = relationship(
        'BetContext',
        back_populates="testing_event",
        uselist=False,
    )
