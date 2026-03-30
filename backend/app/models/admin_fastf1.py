from datetime import datetime
from pydantic import BaseModel

class FastF1SessionPreview(BaseModel):
    order: int
    fastf1_name: str
    session_type: str | None
    scheduled_start_utc: datetime | None


class FastF1RaceEventPreview(BaseModel):
    season_year: int
    round_number: int
    country_name: str
    country_iso2_suggestion: str | None
    event_name: str
    official_event_name: str
    location: str
    event_format: str
    circuit_code_suggestion: str
    scheduled_event_end_utc: datetime | None
    sessions: list[FastF1SessionPreview]

class FastF1RaceEventPreviewListResponse(BaseModel):
    items: list[FastF1RaceEventPreview]