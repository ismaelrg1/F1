from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Country
from app.domain.admin.countries.ports import AdminCountryRepository


class SqlAlchemyAdminCountryRepository(AdminCountryRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_iso2(self, iso2: str):
        stmt = select(Country).where(Country.iso2 == iso2)
        return self._session.execute(stmt).scalar_one_or_none()

    def create(self, *, iso2: str, name: str, flag_asset_url: str | None):
        country = Country(
            iso2=iso2,
            name=name,
            flag_asset_url=flag_asset_url,
        )
        self._session.add(country)
        self._session.commit()
        self._session.refresh(country)
        return country
