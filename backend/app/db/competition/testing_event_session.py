from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Enum, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import TestingEvent
    from app.db.betting import Bet

from app.db.enums import SourceProvider


class TestingEventSession(Base):
    __tablename__ = "testing_event_sessions"
    __table_args__ = (
        UniqueConstraint(
            "testing_event_id",
            "session_order",
            name="uq_testing_event_sessions_event_order",
        ),
        CheckConstraint(
            "session_order >= 1",
            name="ck_testing_event_sessions_order_positive",
        ),
        CheckConstraint(
            "start_datetime IS NULL OR end_datetime IS NULL OR start_datetime < end_datetime",
            name="ck_testing_event_sessions_window_order",
        ),
        CheckConstraint(
            "scheduled_start_datetime IS NULL OR scheduled_end_datetime IS NULL OR scheduled_start_datetime < scheduled_end_datetime",
            name="ck_testing_event_sessions_scheduled_window_order",
        ),
        Index("ix_testing_event_sessions_testing_event_id", "testing_event_id"),
        Index("ix_testing_event_sessions_public_id", "public_id"),
        Index(
            "uq_testing_event_sessions_source",
            "source_provider",
            "source_key",
            unique=True,
            postgresql_where=text("source_key IS NOT NULL"),
        ),
        CheckConstraint(
            "betting_open_at IS NULL OR lock_cutoff IS NULL OR betting_open_at < lock_cutoff",
            name="ck_testing_event_sessions_betting_window_order",
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

    testing_event_id: Mapped[int] = mapped_column(
        ForeignKey("competition.testing_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    session_order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    source_provider: Mapped[SourceProvider] = mapped_column(
        Enum(SourceProvider, name="source_provider_enum", schema="competition", create_type=False),
        nullable=False,
        server_default=text("'MANUAL'"),
    )
    source_key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    start_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    end_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    scheduled_start_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    scheduled_end_datetime: Mapped[Optional[datetime]] = mapped_column(
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

    testing_event: Mapped["TestingEvent"] = relationship(
        "TestingEvent",
        back_populates="sessions",
    )

    bets: Mapped[List["Bet"]] = relationship(
        "Bet",
        back_populates="testing_event_session",
    )
