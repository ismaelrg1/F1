from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class HomeEvent:
    public_id: UUID
    season_year: int
    round_number: int | None
    name: str
    circuit_code: str
    circuit_name: str
    country_name: str
    event_start: datetime | None
    event_end: datetime | None
    scheduled_event_start: datetime | None
    scheduled_event_end: datetime | None
    status: str


@dataclass(frozen=True)
class HomeEventResult:
    kind: Literal["RACE", "TESTING"]
    event: HomeEvent
