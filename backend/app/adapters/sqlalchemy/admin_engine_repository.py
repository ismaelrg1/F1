from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Engine, Season, SeasonEngine
from app.domain.admin.engines.ports import AdminEngineRepository


class SqlAlchemyAdminEngineRepository(AdminEngineRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_code(self, code: str) -> Engine | None:
        stmt = select(Engine).where(Engine.code == code)
        return self._session.execute(stmt).scalar_one_or_none()

    def create(self, *, code: str, name: str) -> Engine:
        engine = Engine(code=code, name=name)
        self._session.add(engine)
        self._session.flush()
        self._session.refresh(engine)
        return engine

    def get_season_by_year(self, year: int) -> Season | None:
        stmt = select(Season).where(Season.year == year)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_season_engine(self, *, season_id: int, engine_id: int) -> SeasonEngine | None:
        stmt = select(SeasonEngine).where(
            SeasonEngine.season_id == season_id,
            SeasonEngine.engine_id == engine_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def create_season_engine(self, *, season_id: int, engine_id: int, is_active: bool) -> SeasonEngine:
        season_engine = SeasonEngine(
            season_id=season_id,
            engine_id=engine_id,
            is_active=is_active,
        )
        self._session.add(season_engine)
        self._session.flush()
        self._session.refresh(season_engine)
        return season_engine