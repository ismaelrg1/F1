from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.management.official_results.errors import (
    OfficialResultsAlreadyExistsError,
    OfficialResultsBetContextNotFoundError,
    OfficialResultsBetScoreNotFoundError,
    OfficialResultsEventSessionNotFoundError,
    OfficialResultsInvalidScopeError,
    OfficialResultsNotFoundError,
    OfficialResultsTestingEventSessionNotFoundError,
    OfficialResultsForbiddenGroupError
)

OFFICIAL_RESULTS_ERROR_MAP = {
    OfficialResultsBetContextNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.official_results.bet_context_not_found",
    ),
    OfficialResultsEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.official_results.event_session_not_found",
    ),
    OfficialResultsTestingEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.official_results.testing_event_session_not_found",
    ),
    OfficialResultsBetScoreNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.official_results.bet_score_not_found",
    ),
    OfficialResultsInvalidScopeError: ErrorCatalogEntry(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="management.official_results.invalid_scope",
    ),
    OfficialResultsAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="management.official_results.already_exists",
    ),
    OfficialResultsNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.official_results.not_found",
    ),
    OfficialResultsForbiddenGroupError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="management.official_results.forbidden_group",
    ),
}