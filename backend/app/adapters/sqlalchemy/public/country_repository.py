from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Country
from app.domain.countries.models import CountryResult
from app.domain.countries.ports import CountryRepository

class SqlAlchemyCountryRepository(CountryRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_countries(self) -> list[CountryResult]:
        stmt = select(Country).order_by(Country.name.asc())
        return [
            self._map_country(country)
            for country in self._session.execute(stmt).scalars().all()
        ]

    @staticmethod
    def _map_country(country: Country) -> CountryResult:
        return CountryResult(
            id=country.id,
            iso2=country.iso2,
            name=country.name,
            flag_asset_url=country.flag_asset_url,
        )
