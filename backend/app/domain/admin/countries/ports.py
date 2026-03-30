from typing import Protocol

from app.db.competition import Country

class AdminCountryRepository(Protocol):
    def get_by_iso2(self, iso2: str) -> Country | None:
        ...

    def create(self, *, iso2: str, name: str, flag_asset_url: str | None) -> Country:
        ...
