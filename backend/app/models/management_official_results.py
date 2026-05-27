from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.scoring.official_result import SourceType
from app.db.enums import BetContextKind, BetValueType, RaceEventStatus, SessionType, TestingEventStatus


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

class OfficialResultQuestionOptionRead(BaseModel):
    value: str
    label: str
    meta: dict[str, Any] | None = None


class OfficialResultQuestionRead(BaseModel):
    code: str
    label: str
    value_type: BetValueType
    required: bool
    display_order: int
    base_points: float
    constraints_json: dict[str, Any] | None
    options: list[OfficialResultQuestionOptionRead] | None
    official_value: str | None = None
    official_source: SourceType | None = None
    official_created_at: datetime | None = None


class OfficialResultScopeStatusRead(BaseModel):
    has_official_results: bool
    results_published: bool
    write_method: Literal["POST", "PATCH"]


class RaceEventOfficialResultsSessionRead(BaseModel):
    event_session_public_id: UUID
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime | None
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    scope_status: OfficialResultScopeStatusRead
    questions: list[OfficialResultQuestionRead]


class RaceEventOfficialResultsResponse(BaseModel):
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    scope_status: OfficialResultScopeStatusRead
    event_questions: list[OfficialResultQuestionRead]
    sessions: list[RaceEventOfficialResultsSessionRead]


class TestingEventOfficialResultsSessionRead(BaseModel):
    testing_event_session_public_id: UUID
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None
    scope_status: OfficialResultScopeStatusRead
    questions: list[OfficialResultQuestionRead]


class TestingEventOfficialResultsResponse(BaseModel):
    kind: BetContextKind
    testing_event_public_id: UUID
    label: str
    status: TestingEventStatus
    scope_status: OfficialResultScopeStatusRead
    event_questions: list[OfficialResultQuestionRead]
    sessions: list[TestingEventOfficialResultsSessionRead]


class SeasonOfficialResultsResponse(BaseModel):
    kind: BetContextKind
    season_year: int
    label: str
    scope_status: OfficialResultScopeStatusRead
    questions: list[OfficialResultQuestionRead]