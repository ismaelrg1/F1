from dataclasses import dataclass

from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.enums import BetContextKind, RaceEventStatus, SessionType, TestingEventStatus

@dataclass(frozen=True)
class BetQuestionOptionResult:
    value: str
    label: str
    meta: dict[str, Any] | None = None


@dataclass(frozen=True)
class BetQuestionResult:
    code: str
    label: str
    value_type: str
    required: bool
    display_order: int
    base_points: float
    constraints_json: dict[str, Any] | None
    options: list[BetQuestionOptionResult] | None


@dataclass(frozen=True)
class RaceEventBetQuestionsSessionResult:
    event_session_public_id: UUID
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    questions: list[BetQuestionResult]


@dataclass(frozen=True)
class RaceEventBetQuestionsResult:
    bet_context_public_id: UUID
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    event_questions: list[BetQuestionResult]
    sessions: list[RaceEventBetQuestionsSessionResult]

@dataclass(frozen=True)
class TestingEventBetQuestionsSessionResult:
    testing_event_session_public_id: UUID
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None
    questions: list[BetQuestionResult]


@dataclass(frozen=True)
class TestingEventBetQuestionsResult:
    bet_context_public_id: UUID
    kind: BetContextKind
    testing_event_public_id: UUID
    label: str
    status: TestingEventStatus
    event_questions: list[BetQuestionResult]
    sessions: list[TestingEventBetQuestionsSessionResult]

