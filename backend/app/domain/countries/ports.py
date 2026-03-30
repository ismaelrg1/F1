from typing import Protocol

from app.db.competition import Country

class CountryRepository(Protocol):
    def list_countries(self) -> list[Country]:
        ...