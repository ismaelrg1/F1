from typing import Protocol

from app.domain.admin.circuits.models import AdminCircuit, AdminCircuitCountry

class AdminCircuitRepository(Protocol):
    def get_by_code(self, code: str) -> AdminCircuit | None:
        ...

    def get_country_by_iso2(self, iso2: str) -> AdminCircuitCountry | None:
        ...

    def create(
        self,
        *,
        code: str,
        name: str,
        country_id: int,
        map_asset_url: str | None,
        image_asset_url: str | None,
    ) -> AdminCircuit:
        ...
