from pydantic import BaseModel, Field

class CircuitCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    country_iso2: str = Field(min_length=2, max_length=2)
    map_asset_url: str | None = Field(default=None, max_length=200)
    image_asset_url: str | None = Field(default=None, max_length=200)

class CircuitCreateResponse(BaseModel):
    id: int
    code: str
    name: str
    country_iso2: str
    map_asset_url: str | None
    image_asset_url: str | None
