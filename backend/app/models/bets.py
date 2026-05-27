from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.db.enums import BetContextKind, BetValueType, RaceEventStatus, SessionType, TestingEventStatus


class BetQuestionOptionRead(BaseModel):
    value: str
    label: str
    meta: dict[str, Any] | None = None

    model_config = {
        "ser_json_exclude_none": True,
    }


class BetQuestionRead(BaseModel):
    code: str
    label: str
    value_type: BetValueType
    required: bool
    display_order: int
    base_points: float
    constraints_json: dict[str, Any] | None
    options: list[BetQuestionOptionRead] | None


class RaceEventBetQuestionsSessionRead(BaseModel):
    event_session_public_id: UUID
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    questions: list[BetQuestionRead]


class RaceEventBetQuestionsResponse(BaseModel):
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    event_questions: list[BetQuestionRead]
    sessions: list[RaceEventBetQuestionsSessionRead]


class TestingEventBetQuestionsSessionRead(BaseModel):
    testing_event_session_public_id: UUID
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None
    questions: list[BetQuestionRead]


class TestingEventBetQuestionsResponse(BaseModel):
    kind: BetContextKind
    testing_event_public_id: UUID
    label: str
    status: TestingEventStatus
    event_questions: list[BetQuestionRead]
    sessions: list[TestingEventBetQuestionsSessionRead]

class SeasonBetQuestionsResponse(BaseModel):
    kind: BetContextKind
    season_year: int
    label: str
    questions: list[BetQuestionRead]

class BetAnswerRead(BaseModel):
    bet_score_code: str
    value: str


class RaceEventBetAnswersSessionResponse(BaseModel):
    event_session_public_id: UUID
    session_type: SessionType
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    answers: list[BetAnswerRead]


class RaceEventBetAnswersResponse(BaseModel):
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    event_answers: list[BetAnswerRead]
    sessions: list[RaceEventBetAnswersSessionResponse]

class TestingEventBetAnswersSessionResponse(BaseModel):
    testing_event_session_public_id: UUID
    session_order: int
    name: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    answers: list[BetAnswerRead]


class TestingEventBetAnswersResponse(BaseModel):
    kind: BetContextKind
    testing_event_public_id: UUID
    label: str
    status: TestingEventStatus
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    event_answers: list[BetAnswerRead]
    sessions: list[TestingEventBetAnswersSessionResponse]

class SeasonBetAnswersResponse(BaseModel):
    kind: BetContextKind
    season_year: int
    label: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    answers: list[BetAnswerRead]

class BetAnswerWrite(BaseModel):
    bet_score_code: str
    value: str


class BetAnswersPatchRequest(BaseModel):
    answers: list[BetAnswerWrite]