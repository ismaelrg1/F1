from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.access.errors import (
    GroupNotFoundError,
    InvalidGroupIdError,
    InvalidSubjectError,
    MissingPermissionsError,
    MissingSubjectError,
    NotGroupMemberError,
    UserNotFoundError,
)

ACCESS_ERROR_MAP = {
    MissingSubjectError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="access.missing_subject",
    ),
    InvalidSubjectError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="access.invalid_subject",
    ),
    UserNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="access.user_not_found",
    ),
    InvalidGroupIdError: ErrorCatalogEntry(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="access.invalid_group_id",
    ),
    GroupNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="access.group_not_found",
    ),
    NotGroupMemberError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="access.not_group_member",
    ),
    MissingPermissionsError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="access.missing_permissions",
    ),
}
