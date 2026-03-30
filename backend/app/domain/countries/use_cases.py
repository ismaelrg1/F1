from app.domain.countries.ports import CountryRepository


class ListCountries:
    def __init__(self, repository: CountryRepository):
        self._repository = repository

    def execute(self):
        return self._repository.list_countries()