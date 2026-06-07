from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.powerups.errors import (
    PowerUpsBetContextNotFoundError,
    PowerUpsRaceEventNotFoundError,
    PowerUpsRaceEventSessionNotFoundError,
    PowerUpsSeasonNotFoundError,
    PowerUpsTestingEventNotFoundError,
    PowerUpsTestingEventSessionNotFoundError,
)


BET_POWERUPS_ERROR_MAP = {
    PowerUpsRaceEventNotFoundError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.powerups.race_event_not_found",
    ),
    PowerUpsTestingEventNotFoundError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.powerups.testing_event_not_found",
    ),
    PowerUpsSeasonNotFoundError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.powerups.season_not_found",
    ),
    PowerUpsBetContextNotFoundError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.powerups.bet_context_not_found",
    ),
    PowerUpsRaceEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.powerups.race_event_session_not_found",
    ),
    PowerUpsTestingEventSessionNotFoundError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.powerups.testing_event_session_not_found",
    ),
}
