from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.db.scoring.official_result import SourceType


class OfficialResultWriteItem(BaseModel):
    bet_score_code: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=255)


class OfficialResultsWriteRequest(BaseModel):
    bet_context_public_id: UUID
    event_session_public_id: UUID | None = None
    testing_event_session_public_id: UUID | None = None
    source: SourceType
    results: list[OfficialResultWriteItem] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scope(self):
        if self.event_session_public_id is not None and self.testing_event_session_public_id is not None:
            raise ValueError("Only one session scope can be provided")
        return self


class OfficialResultRead(BaseModel):
    bet_context_public_id: UUID
    event_session_public_id: UUID | None = None
    testing_event_session_public_id: UUID | None = None
    bet_score_code: str
    label: str
    value: str
    source: SourceType
    created_at: datetime


class OfficialResultsWriteResponse(BaseModel):
    items: list[OfficialResultRead]