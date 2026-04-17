from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Season
from app.domain.admin.seasons.models import AdminSeason
from app.domain.admin.seasons.ports import AdminSeasonRepository


class SqlAlchemyAdminSeasonRepository(AdminSeasonRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_year(self, year: int) -> AdminSeason | None:
        stmt = select(Season).where(Season.year == year)
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None
        return self._map_season(season)

    def get_active_season(self) -> AdminSeason | None:
        stmt = select(Season).where(Season.is_active.is_(True))
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None
        return self._map_season(season)

    def create(self, *, year: int, is_active: bool) -> AdminSeason:
        season = Season(year=year, is_active=is_active)
        self._session.add(season)
        self._session.commit()
        self._session.refresh(season)
        return self._map_season(season)
    
    def list_seasons(self) -> list[AdminSeason]:
        stmt = select(Season).order_by(Season.year.desc())
        seasons = self._session.execute(stmt).scalars().all()
        return [self._map_season(season) for season in seasons]

    @staticmethod
    def _map_season(season: Season) -> AdminSeason:
        return AdminSeason(
            id=season.id,
            year=season.year,
            is_active=season.is_active,
        )