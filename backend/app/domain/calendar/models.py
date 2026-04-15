from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

@dataclass(frozen=True)
class CalendarTestingSession:
    public_id: UUID
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None

@dataclass(frozen=True)
class CalendarRaceSession:
    public_id: UUID
    session_type: str
    start_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime | None
    scheduled_lock_cutoff: datetime | None
    status: str
    status_reason: str | None

@dataclass(frozen=True)
class CalendarEvent:
    id: int
    public_id: UUID
    kind: Literal["TESTING", "RACE"]
    season_year: int
    round_number: int | None
    name: str
    circuit_code: str
    circuit_name: str
    country_name: str
    event_start: datetime | None
    event_end: datetime | None
    scheduled_event_start: datetime | None
    scheduled_event_end: datetime | None
    status: str
    status_reason: str | None
    testing_sessions: tuple[CalendarTestingSession, ...]
    race_sessions: tuple[CalendarRaceSession, ...]


@dataclass(frozen=True)
class CalendarEventResult:
    event: CalendarEvent
    is_up_next: bool
