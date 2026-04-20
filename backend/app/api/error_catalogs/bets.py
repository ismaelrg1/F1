from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    BetContextNotFoundForSeasonError,
    BetContextNotFoundForTestingEventError,
    RaceEventNotFoundForBetQuestionsError,
    RaceEventSessionNotFoundForBetAnswersError,
    SeasonNotFoundForBetQuestionsError,
    TestingEventNotFoundForBetQuestionsError,
    TestingEventSessionNotFoundForBetAnswersError,
    BetAnswersClosedError,
    BetAnswerQuestionNotFoundError,
    BetAlreadySubmittedError,
    BetAnswersNotOpenError,
)

BETS_ERROR_MAP = {
    RaceEventNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.race_event_not_found",
    ),
    RaceEventSessionNotFoundForBetAnswersError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.race_event_session_not_found",
    ),
    BetContextNotFoundForRaceEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.bet_context_not_found_for_race_event",
    ),
    TestingEventNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.testing_event_not_found",
    ),
    TestingEventSessionNotFoundForBetAnswersError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.testing_event_session_not_found",
    ),
    BetContextNotFoundForTestingEventError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.bet_context_not_found_for_testing_event",
    ),
    SeasonNotFoundForBetQuestionsError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.season_not_found",
    ),
    BetContextNotFoundForSeasonError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="bets.bet_context_not_found_for_season",
    ),
    BetAnswersClosedError: ErrorCatalogEntry(
    status_code=status.HTTP_409_CONFLICT,
    error_code="bets.answers_closed",
    ),
    BetAnswerQuestionNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="bets.answer_question_not_found",
    ),
    BetAlreadySubmittedError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="bets.already_submitted",
    ),
    BetAnswersNotOpenError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="bets.answers_not_open",
    ),
}
