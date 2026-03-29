from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.admin.countries.errors import CountryAlreadyExistsError
from app.domain.admin.seasons.errors import (
    ActiveSeasonAlreadyExistsError,
    SeasonAlreadyExistsError,
)

ADMIN_ERROR_MAP = {
    SeasonAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.season_already_exists",
    ),
    ActiveSeasonAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.active_season_already_exists",
    ),
    CountryAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.country_already_exists",
    ),
}
