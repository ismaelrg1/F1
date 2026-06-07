from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventResultsError,
    BetContextNotFoundForSeasonResultsError,
    BetContextNotFoundForTestingEventResultsError,
    RaceEventNotFoundForBetResultsError,
    RaceEventSessionNotFoundForBetResultsError,
    SeasonNotFoundForBetResultsError,
    TestingEventNotFoundForBetResultsError,
    TestingEventSessionNotFoundForBetResultsError,
)


BET_RESULTS_ERROR_MAP = {
    RaceEventNotFoundForBetResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.race_event_not_found",
    ),
    TestingEventNotFoundForBetResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.testing_event_not_found",
    ),
    SeasonNotFoundForBetResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.season_not_found",
    ),
    RaceEventSessionNotFoundForBetResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.race_event_session_not_found",
    ),
    TestingEventSessionNotFoundForBetResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.testing_event_session_not_found",
    ),
    BetContextNotFoundForRaceEventResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.race_event_bet_context_not_found",
    ),
    BetContextNotFoundForTestingEventResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.testing_event_bet_context_not_found",
    ),
    BetContextNotFoundForSeasonResultsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.results.season_bet_context_not_found",
    ),
}
