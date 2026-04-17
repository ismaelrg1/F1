from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.competition import(
    Driver,
    Engine,
    Season,
    SeasonDriver,
    SeasonEngine,
    SeasonTeam, 
    TeamF1,
)
from app.domain.seasons.models import SeasonRoster, SeasonRosterEntry, SeasonSummary
from app.domain.seasons.ports import SeasonRepository


class SqlAlchemySeasonRepository(SeasonRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_seasons(self) -> list[SeasonSummary]:
        stmt = select(Season).order_by(Season.year.desc())
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

    def get_season_roster(self, season_id: int) -> SeasonRoster | None:
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
        return SeasonRoster(
            season_id=season.id,
            drivers=[
                SeasonRosterEntry(code=driver.code, name=driver.name)
                for driver in drivers
            ],
            teams=[
                SeasonRosterEntry(code=team.code, name=team.name)
                for team in teams
            ],
            engines=[
                SeasonRosterEntry(code=engine.code, name=engine.name)
                for engine in engines
            ],
        )

    @staticmethod
    def _map_season(season: Season) -> SeasonSummary:
        return SeasonSummary(
            id=season.id,
            year=season.year,
            is_active=season.is_active,
        )
