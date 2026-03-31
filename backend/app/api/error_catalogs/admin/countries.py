from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry

from app.domain.admin.countries.errors import CountryAlreadyExistsError

ADMIN_COUNTRY_ERROR_MAP = {
    CountryAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.country_already_exists",
    ),
}