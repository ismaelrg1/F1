from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ManagementCalendarCountry:
    name: str
    flag_asset_url: str | None


@dataclass(frozen=True)
class ManagementCalendarSession:
    public_id: UUID
    name: str
    type: str
    has_official_results: bool
    results_published: bool


@dataclass(frozen=True)
class ManagementCalendarEvent:
    type: str
    public_id: UUID
    season_year: int
    round_number: int | None
    name: str
    country: ManagementCalendarCountry
    sessions: tuple[ManagementCalendarSession, ...]
    has_bet_context: bool
    has_official_results: bool
    results_published: bool