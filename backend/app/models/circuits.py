from pydantic import BaseModel, ConfigDict, Field

class CircuitCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    country_id: int
    map_asset_url: str | None = Field(default=None, max_length=200)
    image_asset_url: str | None = Field(default=None, max_length=200)

class CircuitCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    country_id: int
    map_asset_url: str | None
    image_asset_url: str | None