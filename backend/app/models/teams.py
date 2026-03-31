from pydantic import BaseModel, Field


class TeamCreateRequest(BaseModel):
    code: str = Field(min_length=3, max_length=3)
    name: str = Field(min_length=2, max_length=100)


class TeamCreateResponse(BaseModel):
    id: int
    code: str
    name: str


class SeasonTeamCreateRequest(BaseModel):
    season_year: int
    team_code: str = Field(min_length=3, max_length=3)
    is_active: bool = True


class SeasonTeamCreateResponse(BaseModel):
    season_year: int
    team_code: str
    is_active: bool