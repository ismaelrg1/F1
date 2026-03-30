from typing import Protocol

from app.db.competition import Circuit, Country

class AdminCircuitRepository(Protocol):
    def get_by_code(self, code: str) -> Circuit | None:
        ...

    def get_country_by_iso2(self, iso2: str) -> Country | None:
        ...

    def create(
        self,
        *,
        code: str,
        name: str,
        country_id: int,
        map_asset_url: str | None,
        image_asset_url: str | None,
    ) -> Circuit:
        ...
