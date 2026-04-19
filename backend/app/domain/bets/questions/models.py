from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from uuid import UUID

from app.domain.bets.shared.models import (
    BetQuestionResult,
)


@dataclass(frozen=True)
class RaceEventBetQuestionsSessionResult:
    event_session_public_id: UUID
    session_type: str
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: str
    questions: list[BetQuestionResult]

@dataclass(frozen=True)
class RaceEventBetQuestionsResult:
    bet_context_public_id: UUID
    kind: str
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
    kind: str
    testing_event_public_id: UUID
    label: str
    status: str
    event_questions: list[BetQuestionResult]
    sessions: list[TestingEventBetQuestionsSessionResult]


@dataclass(frozen=True)
class SeasonBetQuestionsResult:
    bet_context_public_id: UUID
    kind: str
    season_year: int
    label: str
    questions: list[BetQuestionResult]
