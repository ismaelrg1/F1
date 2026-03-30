from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.admin.countries.errors import CountryAlreadyExistsError
from app.domain.admin.seasons.errors import (
    ActiveSeasonAlreadyExistsError,
    SeasonAlreadyExistsError,
)
from app.domain.admin.circuits.errors import (
    CircuitAlreadyExistsError,
    CountryNotFoundForCircuitError,
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
    CircuitAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.circuit_already_exists",
    ),
    CountryNotFoundForCircuitError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.country_not_found_for_circuit",
    ),
}
