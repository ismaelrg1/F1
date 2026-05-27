from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.db.scoring.official_result import SourceType


class OfficialResultWriteItem(BaseModel):
    bet_score_code: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=255)


class OfficialResultsWriteRequest(BaseModel):
    source: SourceType
    results: list[OfficialResultWriteItem] = Field(min_length=1)


class OfficialResultRead(BaseModel):
    event_session_public_id: UUID | None = None
    testing_event_session_public_id: UUID | None = None
    bet_score_code: str
    label: str
    value: str
    source: SourceType
    created_at: datetime


class OfficialResultsWriteResponse(BaseModel):
    items: list[OfficialResultRead]