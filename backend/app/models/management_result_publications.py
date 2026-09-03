from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResultPublicationWriteRequest(BaseModel):
    note: str | None = Field(default=None, max_length=5000)


class ResultPublicationRead(BaseModel):
    published: bool = True
    reason: str | None = None
    race_event_public_id: UUID | None = None
    event_session_public_id: UUID | None = None
    testing_event_public_id: UUID | None = None
    testing_event_session_public_id: UUID | None = None
    season_year: int | None = None
    published_at: datetime | None = None
    note: str | None = None


class ResultPublicationDeleteResponse(BaseModel):
    deleted: bool
