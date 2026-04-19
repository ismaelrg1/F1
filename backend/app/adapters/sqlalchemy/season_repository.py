from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Season
from app.domain.seasons.models import SeasonSummary
from app.domain.seasons.ports import SeasonRepository


class SqlAlchemySeasonRepository(SeasonRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_seasons(self, *, is_active: bool | None = None) -> list[SeasonSummary]:
        stmt = select(Season)
        
        if is_active is not None:
            stmt = stmt.where(Season.is_active.is_(is_active))
        
        stmt = stmt.order_by(Season.year.desc())
        
        return [
            self._map_season(season)
            for season in self._session.execute(stmt).scalars().all()
        ]
    
    def get_active_season(self) -> SeasonSummary | None:
        stmt = select(Season).where(Season.is_active.is_(True))
        season = self._session.execute(stmt).scalar_one_or_none()
        return None if season is None else self._map_season(season)

    def get_season(self, season_id: int) -> SeasonSummary | None:
        season = self._session.get(Season, season_id)
        return None if season is None else self._map_season(season)

    @staticmethod
    def _map_season(season: Season) -> SeasonSummary:
        return SeasonSummary(
            id=season.id,
            year=season.year,
            is_active=season.is_active,
        )
