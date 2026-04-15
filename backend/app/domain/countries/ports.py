from typing import Protocol

from app.domain.countries.models import CountryResult

class CountryRepository(Protocol):
    def list_countries(self) -> list[CountryResult]:
        ...