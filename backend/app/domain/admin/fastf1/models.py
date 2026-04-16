from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FastF1RaceSessionPreview:
    order: int
    fastf1_name: str | None
    session_type: str | None
    source_provider: str
    source_key: str
    scheduled_start_utc: datetime | None


@dataclass(frozen=True)
class FastF1RaceEventPreview:
    season_year: int
    round_number: int
    country_name: str
    country_iso2_suggestion: str | None
    event_name: str
    official_event_name: str
    location: str
    event_format: str
    source_provider: str
    source_key: str
    circuit_code_suggestion: str
    scheduled_event_end_utc: datetime | None
    sessions: list[FastF1RaceSessionPreview]


@dataclass(frozen=True)
class FastF1TestingSessionPreview:
    order: int
    fastf1_name: str | None
    source_provider: str
    source_key: str
    scheduled_start_utc: datetime | None


@dataclass(frozen=True)
class FastF1TestingEventPreview:
    season_year: int
    country_name: str
    country_iso2_suggestion: str | None
    event_name: str
    official_event_name: str
    location: str
    event_format: str
    source_provider: str
    source_key: str
    circuit_code_suggestion: str
    scheduled_event_end_utc: datetime | None
    sessions: list[FastF1TestingSessionPreview]