from typing import Protocol

from app.domain.admin.countries.models import AdminCountry

class AdminCountryRepository(Protocol):
    def get_by_iso2(self, iso2: str) -> AdminCountry | None:
        ...

    def create(self, *, iso2: str, name: str, flag_asset_url: str | None) -> AdminCountry:
        ...
