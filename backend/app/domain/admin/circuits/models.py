from dataclasses import dataclass


@dataclass(frozen=True)
class AdminCircuitCountry:
    id: int
    iso2: str


@dataclass(frozen=True)
class AdminCircuit:
    id: int
    code: str
    name: str
    country_iso2: str
    map_asset_url: str | None
    image_asset_url: str | None