from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Country
from app.domain.admin.countries.models import AdminCountry
from app.domain.admin.countries.ports import AdminCountryRepository


class SqlAlchemyAdminCountryRepository(AdminCountryRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_iso2(self, iso2: str) -> AdminCountry | None:
        stmt = select(Country).where(Country.iso2 == iso2)
        country = self._session.execute(stmt).scalar_one_or_none()
        if country is None:
            return None
        return self._map_country(country)

    def create(self, *, iso2: str, name: str, flag_asset_url: str | None) -> AdminCountry:
        country = Country(
            iso2=iso2,
            name=name,
            flag_asset_url=flag_asset_url,
        )
        self._session.add(country)
        self._session.commit()
        self._session.refresh(country)
        return self._map_country(country)
    
    def _map_country(self, country: Country) -> AdminCountry:
        return AdminCountry(
            id=country.id,
            iso2=country.iso2,
            name=country.name,
            flag_asset_url=country.flag_asset_url,
        )
