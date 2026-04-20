from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum, DateTime, ForeignKey, Boolean, UniqueConstraint, Index, text, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional, List

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import RaceEvent, DriverEntry
    from app.db.betting import Bet, BetException
    from app.db.scoring import ScoreSession, OfficialResult, ResultPublication, ScoringRule
    from app.db.powerups import PowerUpUse, PowerUpRestriction

from app.db.enums import SessionType, RaceEventStatus, SourceProvider

class EventSession(Base):
    __tablename__ = "event_sessions"
    __table_args__ = (
        # Un mismo GP no puede tener dos Qualy
        UniqueConstraint(
            "race_event_id",
            "session_type",
            name="uq_event_sessions_race_event_session_type",
        ),

        Index("ix_event_sessions_race_event_id", "race_event_id"),
        Index("ix_event_sessions_public_id", "public_id"),
        Index(
            "uq_event_sessions_source",
            "source_provider",
            "source_key",
            unique=True,
            postgresql_where=text("source_key IS NOT NULL"),
        ),

        CheckConstraint(
            "betting_open_at IS NULL OR lock_cutoff IS NULL OR betting_open_at < lock_cutoff",
            name="ck_event_sessions_betting_window_order",
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

    race_event_id: Mapped[int] = mapped_column(
        ForeignKey("competition.race_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    session_type: Mapped[SessionType] = mapped_column(
        Enum(
            SessionType,
            name="event_session_type_enum",
            schema="competition",
            create_type=False,
        ),
        nullable=False,
    )

    source_provider: Mapped[SourceProvider] = mapped_column(
        Enum(SourceProvider, name="source_provider_enum", schema="competition", create_type=False),
        nullable=False,
        server_default=text("'MANUAL'"),
    )
    source_key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    status: Mapped[RaceEventStatus] = mapped_column(
        Enum(RaceEventStatus, name="race_event_status_enum", schema="competition"),
        nullable=False,
        server_default=text("'SCHEDULED'")
        )
    status_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    scheduled_start_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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

    results_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),

    )

    results_published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    race_event: Mapped["RaceEvent"] = relationship(
        'RaceEvent',
        back_populates="event_sessions",
    )

    driver_entries: Mapped[List["DriverEntry"]] = relationship(
        'DriverEntry',
        back_populates="event_session"
    )

    bets: Mapped[List["Bet"]] = relationship(
        'Bet',
        back_populates="event_session"
    )

    bet_exceptions: Mapped[List["BetException"]] = relationship(
        'BetException',
        back_populates="event_session"
    )

    score_sessions: Mapped[List["ScoreSession"]] = relationship(
        'ScoreSession',
        back_populates="event_session",
    )

    scoring_rules: Mapped[list["ScoringRule"]] = relationship(
        "ScoringRule",
        back_populates="event_session",
        cascade="all, delete-orphan",
    )

    official_results: Mapped[list["OfficialResult"]] = relationship(
        'OfficialResult',
        back_populates="event_session",
    )

    result_publications: Mapped[List["ResultPublication"]] = relationship(
        "ResultPublication",
        back_populates="event_session",
    )

    powerup_uses: Mapped[list["PowerUpUse"]] = relationship(
        "PowerUpUse",
        back_populates="event_session",
        cascade="all, delete-orphan",
    )

    powerup_restrictions: Mapped[list["PowerUpRestriction"]] = relationship(
        "PowerUpRestriction",
        back_populates="event_session",
    )
