from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.db.enums import BetContextKind, BetResultsVisibilityMode, RaceEventStatus, ScoreComponentType, SessionType


class BetResultsScopeRead(BaseModel):
    type: str

    race_event_public_id: UUID | None = None
    event_session_public_id: UUID | None = None
    session_type: SessionType | None = None

    testing_event_public_id: UUID | None = None
    testing_event_session_public_id: UUID | None = None
    session_order: int | None = None
    name: str | None = None

    season_year: int | None = None


class BetResultsVisibilityRead(BaseModel):
    mode: BetResultsVisibilityMode
    can_view_group_results: bool
    reason: str
    is_locked: bool
    results_published: bool
    results_published_at: datetime | None
    viewer_submitted: bool


class BetResultsUserRead(BaseModel):
    public_id: UUID
    username: str
    display_name: str | None = None


class BetResultsPointsRead(BaseModel):
    base: float = 0
    powerup: float = 0
    extra: float = 0
    penalty: float = 0
    total: float = 0


class BetResultsComponentRead(BaseModel):
    type: ScoreComponentType
    code: str
    points: float
    applies_to: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


class BetOfficialResultRead(BaseModel):
    bet_score_code: str
    label: str
    value: str
    source: str
    created_at: datetime


class BetResultAnswerRead(BaseModel):
    bet_score_code: str
    label: str
    value: str
    is_invalid: bool
    invalid_reason: str | None = None
    official_value: str | None = None
    is_correct: bool | None = None
    points: BetResultsPointsRead
    components: list[BetResultsComponentRead]


class BetResultScoreRead(BaseModel):
    points: BetResultsPointsRead
    components: list[BetResultsComponentRead]
    computed_at: datetime


class BetResultEntryRead(BaseModel):
    user: BetResultsUserRead
    submitted_at: datetime
    last_modified_at: datetime
    locked_at: datetime | None
    answers: list[BetResultAnswerRead]
    score: BetResultScoreRead | None = None


class RaceEventBetResultsBlockRead(BaseModel):
    scope: BetResultsScopeRead
    visibility: BetResultsVisibilityRead
    official_results: list[BetOfficialResultRead]
    entries: list[BetResultEntryRead]


class RaceEventBetResultsSessionRead(BaseModel):
    event_session_public_id: UUID
    session_type: SessionType
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime | None
    scheduled_lock_cutoff: datetime | None
    status: RaceEventStatus
    visibility: BetResultsVisibilityRead
    official_results: list[BetOfficialResultRead]
    entries: list[BetResultEntryRead]


class RaceEventBetResultsResponse(BaseModel):
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    event_results: RaceEventBetResultsBlockRead
    sessions: list[RaceEventBetResultsSessionRead]


class RaceEventSessionBetResultsResponse(BaseModel):
    kind: BetContextKind
    race_event_public_id: UUID
    label: str
    scope: BetResultsScopeRead
    visibility: BetResultsVisibilityRead
    official_results: list[BetOfficialResultRead]
    entries: list[BetResultEntryRead]

class TestingEventSessionBetResultsResponse(BaseModel):
    kind: BetContextKind
    testing_event_public_id: UUID
    label: str
    scope: BetResultsScopeRead
    visibility: BetResultsVisibilityRead
    official_results: list[BetOfficialResultRead]
    entries: list[BetResultEntryRead]

class SeasonBetResultsResponse(BaseModel):
    kind: BetContextKind
    season_year: int
    label: str
    scope: BetResultsScopeRead
    visibility: BetResultsVisibilityRead
    official_results: list[BetOfficialResultRead]
    entries: list[BetResultEntryRead]