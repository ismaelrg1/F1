from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season, Circuit, DriverEntry, EventSession
    from app.db.betting import BetContext

from app.db.enums import RaceEventStatus, SourceProvider

class RaceEvent(Base):
    __tablename__ = "race_events"
    __table_args__ = (
        Index("ix_race_events_public_id", "public_id"),
        Index("ix_race_events_circuit_id", "circuit_id"),
        UniqueConstraint("season_id", "round_number", name="uq_race_events_season_round"),
        CheckConstraint(
            "event_start IS NULL OR event_end IS NULL OR event_start < event_end",
            name="ck_race_events_event_window_order",
        ),
        CheckConstraint(
            "scheduled_event_start IS NULL OR scheduled_event_end IS NULL OR scheduled_event_start < scheduled_event_end",
            name="ck_race_events_scheduled_window_order",
        ),
        Index(
            "uq_race_events_source",
            "source_provider",
            "source_key",
            unique=True,
            postgresql_where=text("source_key IS NOT NULL"),
        ),
        CheckConstraint(
            "betting_open_at IS NULL OR lock_cutoff IS NULL OR betting_open_at < lock_cutoff",
            name="ck_race_events_betting_window_order",
        ),
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
    
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    circuit_id: Mapped[int] = mapped_column(
        ForeignKey("competition.circuits.id", 
        ondelete="RESTRICT"), 
        nullable=False,
    )
    
    event_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    event_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_event_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_event_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    source_provider: Mapped[SourceProvider] = mapped_column(
        Enum(SourceProvider, name="source_provider_enum", schema="competition"),
        nullable=False,
        server_default=text("'MANUAL'"),
    )
    source_key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    betting_open_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    lock_cutoff: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    scheduled_lock_cutoff: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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
