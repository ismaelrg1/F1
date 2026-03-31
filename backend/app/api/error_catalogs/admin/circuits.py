from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry

from app.domain.admin.circuits.errors import (
    CircuitAlreadyExistsError,
    CountryNotFoundForCircuitError,
)

ADMIN_CIRCUIT_ERROR_MAP = {
    CircuitAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.circuit_already_exists",
    ),
    CountryNotFoundForCircuitError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.country_not_found_for_circuit",
    ),
}