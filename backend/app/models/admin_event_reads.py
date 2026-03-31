from datetime import datetime

from pydantic import BaseModel

from app.db.enums import RaceEventStatus, SessionType, SourceProvider, TestingEventStatus

class AdminRaceEventSessionRead(BaseModel):
    id: int
    session_type: SessionType
    source_provider: SourceProvider
    source_key: str | None
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    status_reason: str | None
    results_published: bool
    results_published_at: datetime | None

class AdminRaceEventRead(BaseModel):
    id: int
    season_year: int
    round_number: int
    circuit_code: str
    name: str
    source_provider: SourceProvider
    source_key: str | None
    event_start: datetime | None
    event_end: datetime | None
    scheduled_event_start: datetime | None
    scheduled_event_end: datetime | None
    status: RaceEventStatus
    status_reason: str | None
    sessions: list[AdminRaceEventSessionRead]

class AdminRaceEventListResponse(BaseModel):
    items: list[AdminRaceEventRead]

class AdminTestingEventSessionRead(BaseModel):
    id: int
    session_order: int
    name: str
    source_provider: SourceProvider
    source_key: str | None
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None


class AdminTestingEventRead(BaseModel):
    id: int
    season_year: int
    circuit_code: str
    name: str
    source_provider: SourceProvider
    source_key: str | None
    event_start: datetime | None
    event_end: datetime | None
    scheduled_event_start: datetime | None
    scheduled_event_end: datetime | None
    status: TestingEventStatus
    status_reason: str | None
    sessions: list[AdminTestingEventSessionRead]


class AdminTestingEventListResponse(BaseModel):
    items: list[AdminTestingEventRead]