from pydantic import BaseModel, Field


class SeasonYearRead(BaseModel):
    year: int


class SeasonYearsResponse(BaseModel):
    items: list[SeasonYearRead]


class SeasonRead(BaseModel):
    id: int
    year: int
    is_active: bool


class SeasonListResponse(BaseModel):
    items: list[SeasonRead]


class SeasonCreateRequest(BaseModel):
    year: int = Field(ge=1950, le=2100)
    is_active: bool = False

class SeasonCreateResponse(BaseModel):
    id: int
    year: int
    is_active: bool
