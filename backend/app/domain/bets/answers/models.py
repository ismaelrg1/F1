from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.bets.shared.models import (
    BetAnswerResult,
)

@dataclass(frozen=True)
class RaceEventBetAnswersSessionResult:
    event_session_public_id: UUID
    session_type: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    answers: list[BetAnswerResult]

@dataclass(frozen=True)
class RaceEventBetAnswersResult:
    bet_context_public_id: UUID
    kind: str
    race_event_public_id: UUID
    label: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    event_answers: list[BetAnswerResult]
    sessions: list[RaceEventBetAnswersSessionResult]

@dataclass(frozen=True)
class TestingEventBetAnswersSessionResult:
    testing_event_session_public_id: UUID
    session_order: int
    name: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    answers: list[BetAnswerResult]


@dataclass(frozen=True)
class TestingEventBetAnswersResult:
    bet_context_public_id: UUID
    kind: str
    testing_event_public_id: UUID
    label: str
    status: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    event_answers: list[BetAnswerResult]
    sessions: list[TestingEventBetAnswersSessionResult]
