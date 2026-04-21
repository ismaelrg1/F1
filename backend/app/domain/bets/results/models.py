from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.enums import BetContextKind, BetResultsVisibilityMode, RaceEventStatus, ScoreComponentType, SessionType


@dataclass(frozen=True)
class BetResultsUser:
    public_id: UUID
    username: str
    display_name: str | None


@dataclass(frozen=True)
class BetResultsPoints:
    base: float = 0
    powerup: float = 0
    extra: float = 0
    penalty: float = 0
    total: float = 0


@dataclass(frozen=True)
class BetResultsComponent:
    type: ScoreComponentType
    code: str
    points: float
    applies_to: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class BetOfficialResult:
    bet_score_code: str
    label: str
    value: str
    source: str
    created_at: datetime


@dataclass(frozen=True)
class BetResultAnswer:
    bet_score_code: str
    label: str
    value: str
    is_invalid: bool
    invalid_reason: str | None
    official_value: str | None
    is_correct: bool | None
    points: BetResultsPoints
    components: list[BetResultsComponent] = field(default_factory=list)


@dataclass(frozen=True)
class BetResultScore:
    points: BetResultsPoints
    components: list[BetResultsComponent]
    computed_at: datetime


@dataclass(frozen=True)
class BetResultEntry:
    user: BetResultsUser
    submitted_at: datetime
    last_modified_at: datetime
    locked_at: datetime | None
    answers: list[BetResultAnswer]
    score: BetResultScore | None


@dataclass(frozen=True)
class BetResultsVisibility:
    mode: BetResultsVisibilityMode
    can_view_group_results: bool
    reason: str
    is_locked: bool
    results_published: bool
    results_published_at: datetime | None
    viewer_submitted: bool


@dataclass(frozen=True)
class BetResultsScope:
    type: str

    race_event_public_id: UUID | None = None
    event_session_public_id: UUID | None = None
    session_type: SessionType | None = None

    testing_event_public_id: UUID | None = None
    testing_event_session_public_id: UUID | None = None
    session_order: int | None = None
    name: str | None = None

    season_year: int | None = None

@dataclass(frozen=True)
class RaceEventBetResultsBlock:
    scope: BetResultsScope
    visibility: BetResultsVisibility
    official_results: list[BetOfficialResult]
    entries: list[BetResultEntry]


@dataclass(frozen=True)
class RaceEventBetResultsSession:
    event_session_public_id: UUID
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime | None
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    visibility: BetResultsVisibility
    official_results: list[BetOfficialResult]
    entries: list[BetResultEntry]


@dataclass(frozen=True)
class RaceEventBetResults:
    bet_context_public_id: UUID
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    event_results: RaceEventBetResultsBlock
    sessions: list[RaceEventBetResultsSession]


@dataclass(frozen=True)
class RaceEventSessionBetResults:
    bet_context_public_id: UUID
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    scope: BetResultsScope
    visibility: BetResultsVisibility
    official_results: list[BetOfficialResult]
    entries: list[BetResultEntry]

    
@dataclass(frozen=True)
class TestingEventSessionBetResults:
    bet_context_public_id: UUID
    kind: BetContextKind
    testing_event_public_id: UUID
    label: str
    scope: BetResultsScope
    visibility: BetResultsVisibility
    official_results: list[BetOfficialResult]
    entries: list[BetResultEntry]

@dataclass(frozen=True)
class SeasonBetResults:
    bet_context_public_id: UUID
    kind: BetContextKind
    season_year: int
    label: str
    scope: BetResultsScope
    visibility: BetResultsVisibility
    official_results: list[BetOfficialResult]
    entries: list[BetResultEntry]