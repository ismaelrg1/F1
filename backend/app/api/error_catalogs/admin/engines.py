from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry

from app.domain.admin.engines.errors import (
    EngineAlreadyExistsError,
    SeasonNotFoundForSeasonEngineError,
    EngineNotFoundForSeasonEngineError,
    SeasonEngineAlreadyExistsError,
)


ADMIN_ENGINE_ERROR_MAP = {
    EngineAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.engine_already_exists",
    ),
    SeasonNotFoundForSeasonEngineError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.season_not_found_for_season_engine",
    ),
    EngineNotFoundForSeasonEngineError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.engine_not_found_for_season_engine",
    ),
    SeasonEngineAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.season_engine_already_exists",
    ),
}