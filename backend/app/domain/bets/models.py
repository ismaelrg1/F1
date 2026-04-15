from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.bets.enums import BetContextKind, BetTemplateScope, BetValueType


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
class BetScoreDefinition:
    id: int
    code: str
    label: str
    base_points: float
    value_type: BetValueType
    constraints_json: dict[str, Any] | None


@dataclass(frozen=True)
class BetTemplateItemDefinition:
    id: int
    required: bool
    display_order: int
    bet_score: BetScoreDefinition


@dataclass(frozen=True)
class BetTemplateDefinition:
    scope: BetTemplateScope
    session_type: str | None
    items: tuple[BetTemplateItemDefinition, ...]


@dataclass(frozen=True)
class BetExceptionDefinition:
    event_session_id: int | None
    bet_score_id: int
    override_points: float | None
    is_disabled: bool | None
    override_constraints_json: dict[str, Any] | None


@dataclass(frozen=True)
class BetContextDefinition:
    public_id: UUID
    kind: BetContextKind
    label: str
    exceptions: tuple[BetExceptionDefinition, ...]


@dataclass(frozen=True)
class BetRosterEntry:
    driver_id: int
    driver_code: str
    driver_name: str
    driver_number: int | None
    team_id: int
    team_code: str
    team_name: str
    engine_id: int
    engine_code: str
    engine_name: str
    seat_index: int
    active_from: datetime | None
    active_to: datetime | None


@dataclass(frozen=True)
class BetRaceEventSession:
    id: int
    public_id: UUID
    session_type: str
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: str
    driver_entries: tuple[BetRosterEntry, ...]


@dataclass(frozen=True)
class BetRaceEvent:
    id: int
    public_id: UUID
    season_id: int
    event_start: datetime | None
    scheduled_event_start: datetime | None
    season_driver_entries: tuple[BetRosterEntry, ...]
    event_driver_entries: tuple[BetRosterEntry, ...]
    sessions: tuple[BetRaceEventSession, ...]


@dataclass(frozen=True)
class BetTestingEventSession:
    id: int
    public_id: UUID
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None


@dataclass(frozen=True)
class BetTestingEvent:
    id: int
    public_id: UUID
    season_id: int
    status: str
    event_start: datetime | None
    scheduled_event_start: datetime | None
    season_driver_entries: tuple[BetRosterEntry, ...]
    sessions: tuple[BetTestingEventSession, ...]


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
