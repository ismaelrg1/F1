from app.domain.countries.models import CountryResult
from app.domain.countries.ports import CountryRepository


class ListCountries:
    def __init__(self, repository: CountryRepository):
        self._repository = repository

    def execute(self) -> list[CountryResult]:
        return self._repository.list_countries()