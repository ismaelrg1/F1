from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.db.enums import RaceEventStatus, SessionType


class CalendarRaceSessionRead(BaseModel):
    public_id: UUID
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    status_reason: str | None


class CalendarTestingSessionRead(BaseModel):
    public_id: UUID
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None


class CalendarEventRead(BaseModel):
    kind: Literal["TESTING", "RACE"]
    public_id: UUID
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
    is_up_next: bool
    testing_sessions: list[CalendarTestingSessionRead]
    race_sessions: list[CalendarRaceSessionRead]


class CalendarResponse(BaseModel):
    items: list[CalendarEventRead]
