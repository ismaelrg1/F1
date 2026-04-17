from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.competition import Season
from app.domain.admin.seasons.models import AdminSeason
from app.domain.admin.seasons.ports import AdminSeasonRepository


class SqlAlchemyAdminSeasonRepository(AdminSeasonRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, season_id: int) -> AdminSeason | None:
        season = self._session.get(Season, season_id)
        if season is None:
            return None
        return self._map_season(season)

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
    
    def list_seasons(self, *, is_active: bool | None = None) -> list[AdminSeason]:
        if is_active is None:
            stmt = select(Season).order_by(Season.year.desc())
        else:
            stmt = select(Season).where(Season.is_active.is_(is_active)).order_by(Season.year.desc())
        
        seasons = self._session.execute(stmt).scalars().all()
        return [self._map_season(season) for season in seasons]
    
    def deactivate_other_seasons(self, *, except_season_id: int) -> None:
        stmt = (
            update(Season)
            .where(Season.id != except_season_id)
            .where(Season.is_active.is_(True))
            .values(is_active=False)
        )
        self._session.execute(stmt)

    def update_is_active(self, *, season_id: int, is_active: bool) -> AdminSeason:
        season = self._session.get(Season, season_id)
        season.is_active = is_active
        self._session.commit()
        self._session.refresh(season)
        return self._map_season(season)

    @staticmethod
    def _map_season(season: Season) -> AdminSeason:
        return AdminSeason(
            id=season.id,
            year=season.year,
            is_active=season.is_active,
        )