from typing import Protocol

from app.domain.admin.engines.models import (
    AdminEngine,
    AdminEngineSeason,
    AdminSeasonEngine,
)


class AdminEngineRepository(Protocol):
    def get_by_code(self, code: str) -> AdminEngine | None:
        ...

    def create(self, *, code: str, name: str) -> AdminEngine:
        ...

    def get_season_by_year(self, year: int) -> AdminEngineSeason | None:
        ...

    def get_season_engine(self, *, season_id: int, engine_id: int) -> AdminSeasonEngine | None:
        ...

    def create_season_engine(self, *, season_id: int, engine_id: int, is_active: bool) -> AdminSeasonEngine:
        ...