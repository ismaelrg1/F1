from datetime import datetime

from pydantic import BaseModel, Field

from app.db.enums import RaceEventStatus, SessionType

class EventSessionCreateRequest(BaseModel):
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None = None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None = None
    status: RaceEventStatus | None = None
    status_reason: str | None = Field(default=None, max_length=200)

class RaceEventCreateRequest(BaseModel):
    season_year: int
    round_number: int = Field(ge=1)
    circuit_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=50)
    event_start: datetime | None = None
    event_end: datetime | None = None
    scheduled_event_start: datetime | None = None
    scheduled_event_end: datetime | None = None
    status: RaceEventStatus | None = None
    status_reason: str | None = Field(default=None, max_length=200)
    sessions: list[EventSessionCreateRequest] = Field(default_factory=list)


class EventSessionCreateResponse(BaseModel):
    id: int
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    status_reason: str | None
    results_published: bool
    results_published_at: datetime | None


class RaceEventCreateResponse(BaseModel):
    id: int
    season_year: int
    round_number: int
    circuit_code: str
    name: str
    event_start: datetime | None
    event_end: datetime | None
    scheduled_event_start: datetime | None
    scheduled_event_end: datetime | None
    status: RaceEventStatus
    status_reason: str | None
    sessions: list[EventSessionCreateResponse]