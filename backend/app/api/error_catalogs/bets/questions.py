from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.errors import (
    RaceEventNotFoundForBetQuestionsError,
    SeasonNotFoundForBetQuestionsError,
    TestingEventNotFoundForBetQuestionsError,
)


BET_QUESTIONS_ERROR_MAP = {
    RaceEventNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.questions.race_event_not_found",
    ),
    TestingEventNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.questions.testing_event_not_found",
    ),
    SeasonNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.questions.season_not_found",
    ),
}
