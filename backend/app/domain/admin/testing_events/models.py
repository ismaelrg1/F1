from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AdminTestingEventSeason:
    id: int
    year: int


@dataclass(frozen=True)
class AdminTestingEventCircuit:
    id: int
    code: str


@dataclass(frozen=True)
class AdminTestingEventSessionWrite:
    session_order: int
    name: str
    source_provider: str
    source_key: str | None
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None


@dataclass(frozen=True)
class AdminTestingEventSession:
    id: int
    public_id: UUID
    session_order: int
    name: str
    source_provider: str
    source_key: str | None
    start_datetime: datetime | None
    end_datetime: datetime | None
    scheduled_start_datetime: datetime | None
    scheduled_end_datetime: datetime | None


@dataclass(frozen=True)
class AdminTestingEvent:
    id: int
    public_id: UUID
    season_year: int
    circuit_code: str
    name: str
    source_provider: str
    source_key: str | None
    event_start: datetime | None
    event_end: datetime | None
    scheduled_event_start: datetime | None
    scheduled_event_end: datetime | None
    status: str
    status_reason: str | None
    sessions: list[AdminTestingEventSession]