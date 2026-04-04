from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.db.enums import BetContextKind, BetValueType, RaceEventStatus, SessionType


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
    bet_context_public_id: UUID
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    event_questions: list[BetQuestionRead]
    sessions: list[RaceEventBetQuestionsSessionRead]
