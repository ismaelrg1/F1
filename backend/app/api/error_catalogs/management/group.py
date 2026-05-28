from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.management.group import (
    ManagementForbiddenGroupError,
    ManagementGroupRequiredError,
)

MANAGEMENT_GROUP_ERROR_MAP = {
    ManagementGroupRequiredError: ErrorCatalogEntry(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="management.group_required",
    ),
    ManagementForbiddenGroupError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="management.forbidden_group",
    ),
}
