from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Country
from app.domain.countries.ports import CountryRepository

class SqlAlchemyCountryRepository(CountryRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_countries(self) -> list[Country]:
        stmt = select(Country).order_by(Country.name.asc())
        return list(self._session.execute(stmt).scalars().all())