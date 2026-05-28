from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.management.result_publications.errors import (
    ResultPublicationAlreadyExistsError,
    ResultPublicationBetContextNotFoundError,
    ResultPublicationEventSessionNotFoundError,
    ResultPublicationNotFoundError,
    ResultPublicationOfficialResultsNotFoundError,
    ResultPublicationTestingEventSessionNotFoundError,
    ResultPublicationForbiddenGroupError,
)

RESULT_PUBLICATIONS_ERROR_MAP = {
    ResultPublicationForbiddenGroupError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="management.result_publications.forbidden_group",
    ),
    ResultPublicationBetContextNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.result_publications.bet_context_not_found",
    ),
    ResultPublicationEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.result_publications.event_session_not_found",
    ),
    ResultPublicationTestingEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.result_publications.testing_event_session_not_found",
    ),
    ResultPublicationOfficialResultsNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="management.result_publications.official_results_not_found",
    ),
    ResultPublicationAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="management.result_publications.already_exists",
    ),
    ResultPublicationNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.result_publications.not_found",
    ),
}