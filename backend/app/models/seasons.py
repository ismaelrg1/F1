from pydantic import BaseModel, ConfigDict, Field


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


class SeasonCreateRequest(BaseModel):
    year: int = Field(ge=1950, le=2100)
    is_active: bool = False

class SeasonCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    is_active: bool