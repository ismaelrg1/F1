from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AdminRaceEventSeason:
    id: int
    year: int


@dataclass(frozen=True)
class AdminRaceEventCircuit:
    id: int
    code: str


@dataclass(frozen=True)
class AdminRaceEventSessionWrite:
    session_type: str
    source_provider: str
    source_key: str | None
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: str | None
    status_reason: str | None


@dataclass(frozen=True)
class AdminRaceEventSession:
    id: int
    public_id: UUID
    session_type: str
    source_provider: str
    source_key: str | None
    start_datetime: datetime
    scheduled_start_datetime: datetime | None
    lock_cutoff: datetime
    scheduled_lock_cutoff: datetime | None
    status: str
    status_reason: str | None
    results_published: bool
    results_published_at: datetime | None


@dataclass(frozen=True)
class AdminRaceEvent:
    id: int
    public_id: UUID
    season_year: int
    round_number: int
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
    sessions: list[AdminRaceEventSession]