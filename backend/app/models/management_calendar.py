from uuid import UUID

from pydantic import BaseModel


class ManagementCalendarCountryRead(BaseModel):
    name: str
    flag_asset_url: str | None


class ManagementCalendarSessionRead(BaseModel):
    public_id: UUID
    name: str
    type: str
    has_official_results: bool
    results_published: bool


class ManagementCalendarEventRead(BaseModel):
    type: str
    public_id: UUID
    season_year: int
    round_number: int | None
    name: str
    country: ManagementCalendarCountryRead
    sessions: list[ManagementCalendarSessionRead]
    has_bet_context: bool
    has_official_results: bool
    results_published: bool


class ManagementCalendarResponse(BaseModel):
    items: list[ManagementCalendarEventRead]