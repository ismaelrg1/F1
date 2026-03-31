from datetime import datetime
from typing import Literal

from pydantic import BaseModel

class HomeNextEventRead(BaseModel):
    id: int
    event_kind: Literal["RACE", "TESTING"]
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


class HomeResponse(BaseModel):
    next_event: HomeNextEventRead | None
