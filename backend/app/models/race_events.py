from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.db.enums import RaceEventStatus, SessionType, SourceProvider

class EventSessionCreateRequest(BaseModel):
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None = None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None = None
    source_provider: SourceProvider = SourceProvider.MANUAL
    source_key: str | None = None
    status: RaceEventStatus | None = None
    status_reason: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_provider == SourceProvider.FASTF1 and not self.source_key:
            raise ValueError("source_key is required when source_provider is FASTF1")
        if self.source_provider == SourceProvider.MANUAL and self.source_key is not None:
            raise ValueError("source_key must be null when source_provider is MANUAL")
        return self

class RaceEventCreateRequest(BaseModel):
    season_year: int
    round_number: int = Field(ge=1)
    circuit_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=50)
    event_start: datetime | None = None
    event_end: datetime | None = None
    scheduled_event_start: datetime | None = None
    scheduled_event_end: datetime | None = None
    source_provider: SourceProvider = SourceProvider.MANUAL
    source_key: str | None = None
    status: RaceEventStatus | None = None
    status_reason: str | None = Field(default=None, max_length=200)
    sessions: list[EventSessionCreateRequest] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_provider == SourceProvider.FASTF1 and not self.source_key:
            raise ValueError("source_key is required when source_provider is FASTF1")
        if self.source_provider == SourceProvider.MANUAL and self.source_key is not None:
            raise ValueError("source_key must be null when source_provider is MANUAL")
        return self


class EventSessionCreateResponse(BaseModel):
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


class RaceEventCreateResponse(BaseModel):
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
    sessions: list[EventSessionCreateResponse]
