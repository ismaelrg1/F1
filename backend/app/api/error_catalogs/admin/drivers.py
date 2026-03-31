from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry

from app.domain.admin.drivers.errors import (
    DriverAlreadyExistsError,
    DriverNotFoundForSeasonDriverError,
    SeasonDriverAlreadyExistsError,
    SeasonNotFoundForSeasonDriverError,
)

ADMIN_DRIVER_ERROR_MAP = {
    DriverAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.driver_already_exists",
    ),
    SeasonNotFoundForSeasonDriverError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.season_not_found_for_season_driver",
    ),
    DriverNotFoundForSeasonDriverError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.driver_not_found_for_season_driver",
    ),
    SeasonDriverAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.season_driver_already_exists",
    ),
}