from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    BetContextNotFoundForTestingEventError,
    RaceEventNotFoundForBetQuestionsError,
    TestingEventNotFoundForBetQuestionsError,
)

BETS_ERROR_MAP = {
    RaceEventNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.race_event_not_found",
    ),
    BetContextNotFoundForRaceEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.bet_context_not_found_for_race_event",
    ),
    TestingEventNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.testing_event_not_found",
    ),
    BetContextNotFoundForTestingEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.bet_context_not_found_for_testing_event",
    ),
}
