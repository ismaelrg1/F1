from app.domain.admin.engines.errors import (
    EngineAlreadyExistsError,
    EngineNotFoundForSeasonEngineError,
    SeasonEngineAlreadyExistsError,
    SeasonNotFoundForSeasonEngineError,
)
from app.domain.admin.engines.ports import AdminEngineRepository


class CreateEngine:
    def __init__(self, repository: AdminEngineRepository):
        self._repository = repository

    def execute(self, *, code: str, name: str):
        normalized_code = code.strip().upper()

        existing = self._repository.get_by_code(normalized_code)
        if existing is not None:
            raise EngineAlreadyExistsError(code=normalized_code)

        return self._repository.create(code=normalized_code, name=name)


class CreateSeasonEngine:
    def __init__(self, repository: AdminEngineRepository):
        self._repository = repository

    def execute(self, *, season_year: int, engine_code: str, is_active: bool):
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForSeasonEngineError(season_year=season_year)

        normalized_engine_code = engine_code.strip().upper()
        engine = self._repository.get_by_code(normalized_engine_code)
        if engine is None:
            raise EngineNotFoundForSeasonEngineError(engine_code=normalized_engine_code)

        existing = self._repository.get_season_engine(season_id=season.id, engine_id=engine.id)
        if existing is not None:
            raise SeasonEngineAlreadyExistsError(
                season_year=season.year,
                engine_code=normalized_engine_code,
            )

        return self._repository.create_season_engine(
            season_id=season.id,
            engine_id=engine.id,
            is_active=is_active,
        )