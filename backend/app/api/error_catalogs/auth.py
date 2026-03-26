from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.auth.errors import (
    GoogleAccountNotRegisteredError,
    GoogleEmailNotVerifiedError,
    InvalidAccessTokenError,
    InvalidGoogleTokenError,
    MissingRefreshSubjectError,
    InvalidRefreshTokenError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InactiveUserError,
    MissingAccessTokenError,
    MissingRefreshTokenError,
    UserAlreadyExistsError,
)

AUTH_ERROR_MAP = {
    InvalidCredentialsError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="auth.invalid_credentials",
    ),
    InactiveUserError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="auth.inactive_user",
    ),
    MissingRefreshSubjectError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="auth.missing_refresh_subject",
    ),
    UserAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="auth.user_already_exists",
    ),
    MissingAccessTokenError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="auth.missing_access_token",
    ),
    InvalidAccessTokenError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="auth.invalid_access_token",
    ),
    MissingRefreshTokenError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="auth.missing_refresh_token",
    ),
    InvalidRefreshTokenError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="auth.invalid_refresh_token",
    ),
    InvalidGoogleTokenError: ErrorCatalogEntry(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="auth.invalid_google_token",
    ),
    GoogleEmailNotVerifiedError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="auth.google_email_not_verified",
    ),
    GoogleAccountNotRegisteredError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="auth.google_account_not_registered",
    ),
    InvalidPasswordResetTokenError: ErrorCatalogEntry(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="auth.invalid_password_reset_token",
    ),
}
