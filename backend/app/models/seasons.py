from pydantic import BaseModel, ConfigDict


class SeasonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    is_active: bool


class SeasonListResponse(BaseModel):
    items: list[SeasonRead]


class SeasonRosterEntry(BaseModel):
    code: str
    name: str


class SeasonRosterResponse(BaseModel):
    season_id: int
    drivers: list[SeasonRosterEntry]
    teams: list[SeasonRosterEntry]
    engines: list[SeasonRosterEntry]
