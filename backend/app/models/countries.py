from pydantic import BaseModel, ConfigDict, Field

class CountryCreateRequest(BaseModel):
    iso2: str = Field(min_length=2, max_length=2)
    name: str = Field(min_length=1, max_length=50)
    flag_asset_url: str | None = Field(default=None, max_length=200)


class CountryCreateResponse(BaseModel):
    id: int
    iso2: str
    name: str
    flag_asset_url: str | None


class CountryRead(BaseModel):
    id: int
    iso2: str
    name: str
    flag_asset_url: str | None

class CountryListResponse(BaseModel):
    items: list[CountryRead]
