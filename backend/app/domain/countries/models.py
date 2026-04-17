from dataclasses import dataclass


@dataclass(frozen=True)
class CountryResult:
    id: int
    iso2: str
    name: str
    flag_asset_url: str | None
