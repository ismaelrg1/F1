from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.db.enums import TestingEventStatus, SourceProvider


class TestingEventSessionCreateRequest(BaseModel):
    session_order: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=50)
    source_provider: SourceProvider = SourceProvider.MANUAL
    source_key: str | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    scheduled_start_datetime: datetime | None = None
    scheduled_end_datetime: datetime | None = None

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_provider == SourceProvider.FASTF1 and not self.source_key:
            raise ValueError("source_key is required when source_provider is FASTF1")
        if self.source_provider == SourceProvider.MANUAL and self.source_key is not None:
            raise ValueError("source_key must be null when source_provider is MANUAL")
        return self


class TestingEventCreateRequest(BaseModel):
    season_year: int
    circuit_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=50)
    event_start: datetime | None = None
    event_end: datetime | None = None
    scheduled_event_start: datetime | None = None
    scheduled_event_end: datetime | None = None
    source_provider: SourceProvider = SourceProvider.MANUAL
    source_key: str | None = None
    status: TestingEventStatus | None = None
    status_reason: str | None = Field(default=None, max_length=200)
    sessions: list[TestingEventSessionCreateRequest] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_provider == SourceProvider.FASTF1 and not self.source_key:
            raise ValueError("source_key is required when source_provider is FASTF1")
        if self.source_provider == SourceProvider.MANUAL and self.source_key is not None:
            raise ValueError("source_key must be null when source_provider is MANUAL")
        return self


class TestingEventSessionCreateResponse(BaseModel):
    id: int
    session_order: int
    name: str
    source_provider: SourceProvider
    source_key: str | None
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None


class TestingEventCreateResponse(BaseModel):
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
    sessions: list[TestingEventSessionCreateResponse]
