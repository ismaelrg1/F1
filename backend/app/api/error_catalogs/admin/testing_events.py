from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry

from app.domain.admin.testing_events.errors import (
    CircuitNotFoundForTestingEventError,
    DuplicateTestingEventSessionOrderError,
    SeasonNotFoundForTestingEventError,
    TestingEventAlreadyExistsError,
    TestingEventNotFoundError,
)

ADMIN_TESTING_EVENT_ERROR_MAP = {
    SeasonNotFoundForTestingEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.season_not_found_for_testing_event",
    ),
    CircuitNotFoundForTestingEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.circuit_not_found_for_testing_event",
    ),
    TestingEventAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.testing_event_already_exists",
    ),
    DuplicateTestingEventSessionOrderError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.duplicate_testing_event_session_order",
    ),
    TestingEventNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.testing_event_not_found",
    ),
}