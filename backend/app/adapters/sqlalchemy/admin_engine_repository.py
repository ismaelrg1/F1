from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.competition import Engine, Season, SeasonEngine
from app.domain.admin.engines.models import (
    AdminEngine,
    AdminEngineSeason,
    AdminSeasonEngine,
)
from app.domain.admin.engines.ports import AdminEngineRepository


class SqlAlchemyAdminEngineRepository(AdminEngineRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_code(self, code: str) -> AdminEngine | None:
        stmt = select(Engine).where(Engine.code == code)
        engine = self._session.execute(stmt).scalar_one_or_none()
        if engine is None:
            return None
        return AdminEngine(
            id=engine.id,
            code=engine.code,
            name=engine.name,
        )

    def create(self, *, code: str, name: str) -> AdminEngine:
        engine = Engine(code=code, name=name)
        self._session.add(engine)
        self._session.flush()
        self._session.refresh(engine)
        return AdminEngine(
            id=engine.id,
            code=engine.code,
            name=engine.name,
        )

    def get_season_by_year(self, year: int) -> AdminEngineSeason | None:
        stmt = select(Season).where(Season.year == year)
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None
        return AdminEngineSeason(
            id=season.id,
            year=season.year,
        )

    def get_season_engine(self, *, season_id: int, engine_id: int) -> AdminSeasonEngine | None:
        stmt = (
            select(SeasonEngine)
            .where(
                SeasonEngine.season_id == season_id,
                SeasonEngine.engine_id == engine_id,
            )
            .options(
                joinedload(SeasonEngine.season),
                joinedload(SeasonEngine.engine),
            )
        )
        season_engine = self._session.execute(stmt).scalar_one_or_none()
        if season_engine is None:
            return None
        return self._map_season_engine(season_engine)

    def create_season_engine(
        self,
        *,
        season_id: int,
        engine_id: int,
        is_active: bool,
    ) -> AdminSeasonEngine:
        season_engine = SeasonEngine(
            season_id=season_id,
            engine_id=engine_id,
            is_active=is_active,
        )
        self._session.add(season_engine)
        self._session.flush()

        stmt = (
            select(SeasonEngine)
            .where(
                SeasonEngine.season_id == season_engine.season_id,
                SeasonEngine.engine_id == season_engine.engine_id,
            )
            .options(
                joinedload(SeasonEngine.season),
                joinedload(SeasonEngine.engine),
            )
        )
        created = self._session.execute(stmt).scalar_one()
        return self._map_season_engine(created)

    @staticmethod
    def _map_season_engine(season_engine: SeasonEngine) -> AdminSeasonEngine:
        return AdminSeasonEngine(
            season_year=season_engine.season.year,
            engine_code=season_engine.engine.code,
            is_active=season_engine.is_active,
        )