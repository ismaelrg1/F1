from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry

from app.domain.admin.race_events.errors import (
    CircuitNotFoundForRaceEventError,
    DuplicateRaceEventSessionTypeError,
    RaceEventAlreadyExistsError,
    RaceEventNotFoundError,
    SeasonNotFoundForRaceEventError,
)

ADMIN_RACE_EVENT_ERROR_MAP = {
    SeasonNotFoundForRaceEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.season_not_found_for_race_event",
    ),
    CircuitNotFoundForRaceEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.circuit_not_found_for_race_event",
    ),
    RaceEventAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.race_event_already_exists",
    ),
    DuplicateRaceEventSessionTypeError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.duplicate_race_event_session_type",
    ),
    RaceEventNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.race_event_not_found",
    ),
}