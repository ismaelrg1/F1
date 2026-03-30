from app.domain.admin.circuits.errors import (
    CircuitAlreadyExistsError,
    CountryNotFoundForCircuitError,
)
from app.domain.admin.circuits.ports import AdminCircuitRepository

class CreateCircuit:
    def __init__(self, repository: AdminCircuitRepository):
        self._repository = repository

    def execute(
        self,
        *,
        code: str,
        name: str,
        country_iso2: str,
        map_asset_url: str | None,
        image_asset_url: str | None,
    ):
        normalized_code = code.strip().lower()
        normalized_country_iso2 = country_iso2.strip().upper()

        existing = self._repository.get_by_code(normalized_code)
        if existing is not None:
            raise CircuitAlreadyExistsError(code=normalized_code)
        
        country = self._repository.get_country_by_iso2(normalized_country_iso2)
        if country is None:
            raise CountryNotFoundForCircuitError(country_iso2=normalized_country_iso2)
        
        return self._repository.create(
            code=normalized_code,
            name=name.strip(),
            country_id=country.id,
            map_asset_url=map_asset_url.strip() if map_asset_url else None,
            image_asset_url=image_asset_url.strip() if image_asset_url else None,
        )
