from datetime import datetime

from pydantic import BaseModel, Field

from app.db.enums import TestingEventStatus


class TestingEventSessionCreateRequest(BaseModel):
    session_order: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=50)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    scheduled_start_datetime: datetime | None = None
    scheduled_end_datetime: datetime | None = None


class TestingEventCreateRequest(BaseModel):
    season_year: int
    circuit_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=50)
    event_start: datetime | None = None
    event_end: datetime | None = None
    scheduled_event_start: datetime | None = None
    scheduled_event_end: datetime | None = None
    status: TestingEventStatus | None = None
    status_reason: str | None = Field(default=None, max_length=200)
    sessions: list[TestingEventSessionCreateRequest] = Field(default_factory=list)


class TestingEventSessionCreateResponse(BaseModel):
    id: int
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None


class TestingEventCreateResponse(BaseModel):
    id: int
    season_year: int
    circuit_code: str
    name: str
    event_start: datetime | None
    event_end: datetime | None
    scheduled_event_start: datetime | None
    scheduled_event_end: datetime | None
    status: TestingEventStatus
    status_reason: str | None
    sessions: list[TestingEventSessionCreateResponse]