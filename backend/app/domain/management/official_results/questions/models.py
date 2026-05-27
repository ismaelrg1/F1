from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from app.db.scoring.official_result import SourceType


@dataclass(frozen=True)
class OfficialResultScopeKey:
    event_session_public_id: UUID | None
    testing_event_session_public_id: UUID | None


@dataclass(frozen=True)
class ExistingOfficialResult:
    event_session_public_id: UUID | None
    testing_event_session_public_id: UUID | None
    bet_score_code: str
    value: str
    source: SourceType
    created_at: datetime


@dataclass(frozen=True)
class OfficialResultQuestion:
    code: str
    label: str
    value_type: str
    required: bool
    display_order: int
    base_points: float
    constraints_json: dict[str, Any] | None
    options: list[Any] | None
    official_value: str | None
    official_source: SourceType | None
    official_created_at: datetime | None


@dataclass(frozen=True)
class OfficialResultScopeStatus:
    has_official_results: bool
    results_published: bool
    write_method: Literal["POST", "PATCH"]


@dataclass(frozen=True)
class RaceEventOfficialResultsSession:
    event_session_public_id: UUID
    session_type: str
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime | None
    scheduled_lock_cutoff: datetime | None
    status: str
    scope_status: OfficialResultScopeStatus
    questions: list[OfficialResultQuestion]


@dataclass(frozen=True)
class RaceEventOfficialResultsForm:
    kind: str
    race_event_public_id: UUID
    label: str
    scope_status: OfficialResultScopeStatus
    event_questions: list[OfficialResultQuestion]
    sessions: list[RaceEventOfficialResultsSession]


@dataclass(frozen=True)
class TestingEventOfficialResultsSession:
    testing_event_session_public_id: UUID
    session_order: int
    name: str
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None
    scope_status: OfficialResultScopeStatus
    questions: list[OfficialResultQuestion]


@dataclass(frozen=True)
class TestingEventOfficialResultsForm:
    kind: str
    testing_event_public_id: UUID
    label: str
    status: str
    scope_status: OfficialResultScopeStatus
    event_questions: list[OfficialResultQuestion]
    sessions: list[TestingEventOfficialResultsSession]


@dataclass(frozen=True)
class SeasonOfficialResultsForm:
    kind: str
    season_year: int
    label: str
    scope_status: OfficialResultScopeStatus
    questions: list[OfficialResultQuestion]