from pydantic import BaseModel, Field


class EngineCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=10)
    name: str = Field(min_length=2, max_length=100)


class EngineCreateResponse(BaseModel):
    id: int
    code: str
    name: str


class SeasonEngineCreateRequest(BaseModel):
    season_year: int
    engine_code: str = Field(min_length=2, max_length=10)
    is_active: bool = True


class SeasonEngineCreateResponse(BaseModel):
    season_year: int
    engine_code: str
    is_active: bool