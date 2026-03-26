from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.competition import Driver, Engine, Season, SeasonDriver, SeasonEngine, SeasonTeam, TeamF1
from app.domain.seasons.ports import SeasonRepository


class SqlAlchemySeasonRepository(SeasonRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_seasons(self):
        stmt = select(Season).order_by(Season.year.desc())
        return list(self._session.execute(stmt).scalars().all())

    def get_active_season(self):
        stmt = select(Season).where(Season.is_active.is_(True))
        return self._session.execute(stmt).scalar_one_or_none()

    def get_season(self, season_id: int):
        return self._session.get(Season, season_id)

    def get_season_roster(self, season_id: int):
        stmt = (
            select(Season)
            .where(Season.id == season_id)
            .options(
                selectinload(Season.season_drivers).selectinload(SeasonDriver.driver),
                selectinload(Season.season_teams).selectinload(SeasonTeam.team),
                selectinload(Season.season_engines).selectinload(SeasonEngine.engine),
            )
        )
        season = self._session.execute(stmt).scalar_one_or_none()
        if not season:
            return None

        drivers: list[Driver] = [item.driver for item in season.season_drivers if item.driver]
        teams: list[TeamF1] = [item.team for item in season.season_teams if item.team]
        engines: list[Engine] = [item.engine for item in season.season_engines if item.engine]
        return {"drivers": drivers, "teams": teams, "engines": engines}
