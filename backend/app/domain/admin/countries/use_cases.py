from app.domain.admin.countries.errors import CountryAlreadyExistsError
from app.domain.admin.countries.ports import AdminCountryRepository


class CreateCountry:
    def __init__(self, repository: AdminCountryRepository):
        self._repository = repository

    def execute(
        self,
        *,
        iso2: str,
        name: str,
        flag_asset_url: str | None,
    ):
        normalized_iso2 = iso2.strip().upper()

        existing = self._repository.get_by_iso2(normalized_iso2)
        if existing is not None:
            raise CountryAlreadyExistsError(iso2=normalized_iso2)

        return self._repository.create(
            iso2=normalized_iso2,
            name=name.strip(),
            flag_asset_url=flag_asset_url.strip() if flag_asset_url else None,
        )
