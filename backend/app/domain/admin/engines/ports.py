from typing import Protocol

from app.db.competition import Engine, Season, SeasonEngine


class AdminEngineRepository(Protocol):
    def get_by_code(self, code: str) -> Engine | None:
        ...

    def create(self, *, code: str, name: str) -> Engine:
        ...

    def get_season_by_year(self, year: int) -> Season | None:
        ...

    def get_season_engine(self, *, season_id: int, engine_id: int) -> SeasonEngine | None:
        ...

    def create_season_engine(self, *, season_id: int, engine_id: int, is_active: bool) -> SeasonEngine:
        ...