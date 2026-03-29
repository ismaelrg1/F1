from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Season
from app.domain.admin.seasons.ports import AdminSeasonRepository


class SqlAlchemyAdminSeasonRepository(AdminSeasonRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_year(self, year: int):
        stmt = select(Season).where(Season.year == year)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_active_season(self):
        stmt = select(Season).where(Season.is_active.is_(True))
        return self._session.execute(stmt).scalar_one_or_none()

    def create(self, *, year: int, is_active: bool):
        season = Season(year=year, is_active=is_active)
        self._session.add(season)
        self._session.commit()
        self._session.refresh(season)
        return season
