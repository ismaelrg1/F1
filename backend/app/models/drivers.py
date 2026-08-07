from pydantic import BaseModel, Field

from app.db.enums import SeasonDriverStatus


class DriverCreateRequest(BaseModel):
    code: str = Field(min_length=3, max_length=3)
    name: str = Field(min_length=2, max_length=100)
    nationality_country_id: int | None = None

class DriverCreateResponse(BaseModel):
    id: int
    code: str
    name: str
    nationality_country_id: int | None = None


class SeasonDriverCreateRequest(BaseModel):
    season_year: int
    driver_code: str = Field(min_length=3, max_length=3)
    status: SeasonDriverStatus = SeasonDriverStatus.PRIMARY


class SeasonDriverCreateResponse(BaseModel):
    season_year: int
    driver_code: str
    status: SeasonDriverStatus