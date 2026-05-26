from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.admin.official_results.errors import (
    OfficialResultsAlreadyExistsError,
    OfficialResultsBetContextNotFoundError,
    OfficialResultsBetScoreNotFoundError,
    OfficialResultsEventSessionNotFoundError,
    OfficialResultsInvalidScopeError,
    OfficialResultsNotFoundError,
    OfficialResultsTestingEventSessionNotFoundError,
)

ADMIN_OFFICIAL_RESULTS_ERROR_MAP = {
    OfficialResultsBetContextNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.official_results.bet_context_not_found",
    ),
    OfficialResultsEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.official_results.event_session_not_found",
    ),
    OfficialResultsTestingEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.official_results.testing_event_session_not_found",
    ),
    OfficialResultsBetScoreNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.official_results.bet_score_not_found",
    ),
    OfficialResultsInvalidScopeError: ErrorCatalogEntry(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="admin.official_results.invalid_scope",
    ),
    OfficialResultsAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.official_results.already_exists",
    ),
    OfficialResultsNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.official_results.not_found",
    ),
}