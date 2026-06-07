from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    BetContextNotFoundForSeasonError,
    BetContextNotFoundForTestingEventError,
)


BET_GENERIC_ERROR_MAP = {
    BetContextNotFoundForRaceEventError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.generic.race_event_bet_context_not_found",
    ),
    BetContextNotFoundForTestingEventError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.generic.testing_event_bet_context_not_found",
    ),
    BetContextNotFoundForSeasonError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.generic.season_bet_context_not_found",
    ),
}
