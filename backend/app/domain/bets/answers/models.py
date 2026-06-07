from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.bets.models import (
    # Shared    
    BetAnswerResult,
)

from app.db.enums import PowerUpTargetType

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

@dataclass(frozen=True)
class SeasonBetAnswersResult:
    bet_context_public_id: UUID
    kind: str
    season_year: int
    label: str
    submitted_at: datetime | None
    last_modified_at: datetime | None
    locked_at: datetime | None
    answers: list[BetAnswerResult]

@dataclass(frozen=True)
class BetAnswerInput:
    bet_score_code: str
    value: str

@dataclass(frozen=True)
class BetPowerUpTargetInput:
    target_type: str
    target_user_public_id: UUID | None = None
    target_team_public_id: UUID | None = None
    target_group_public_id: UUID | None = None
    rule_json: dict | None = None

@dataclass(frozen=True)
class BetPowerUpUseInput:
    powerup_code: str
    targets: list[BetPowerUpTargetInput]
    rule_json: dict | None = None

@dataclass(frozen=True)
class BetPowerUpAssignmentDefinition:
    powerup_id: int
    code: str
    name: str
    is_enabled: bool
    target_mode: str
    quantity: int


@dataclass(frozen=True)
class ResolvedBetPowerUpTarget:
    target_type: str
    target_user_id: int | None = None
    target_team_id: int | None = None
    target_group_id: int | None = None
    rule_json: dict | None = None


@dataclass(frozen=True)
class ResolvedBetPowerUpUse:
    powerup_id: int
    rule_json: dict | None
    targets: list[ResolvedBetPowerUpTarget]