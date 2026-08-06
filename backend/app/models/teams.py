from pydantic import BaseModel, Field


class TeamCreateRequest(BaseModel):
    code: str = Field(min_length=3, max_length=3)
    name: str = Field(min_length=2, max_length=100)
    color: str = Field(min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")


class TeamCreateResponse(BaseModel):
    id: int
    code: str
    name: str
    color: str


class SeasonTeamCreateRequest(BaseModel):
    season_year: int
    team_code: str = Field(min_length=3, max_length=3)
    is_active: bool = True


class SeasonTeamCreateResponse(BaseModel):
    season_year: int
    team_code: str
    is_active: bool
