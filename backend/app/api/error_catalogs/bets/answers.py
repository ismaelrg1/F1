from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.errors import (
    BetAlreadySubmittedError,
    BetAnswerQuestionNotFoundError,
    BetAnswersClosedError,
    BetAnswersNotOpenError,
    BetModificationLimitReachedError,
    BetRequiredAnswerMissingError,
    RaceEventNotFoundForBetAnswersError,
    RaceEventSessionNotFoundForBetAnswersError,
    SeasonNotFoundForBetAnswersError,
    TestingEventNotFoundForBetAnswersError,
    TestingEventSessionNotFoundForBetAnswersError,
    BetAnswerRelationViolationError,
)


BET_ANSWERS_ERROR_MAP = {
    RaceEventNotFoundForBetAnswersError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.answers.race_event_not_found",
    ),
    TestingEventNotFoundForBetAnswersError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.answers.testing_event_not_found",
    ),
    SeasonNotFoundForBetAnswersError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.answers.season_not_found",
    ),
    RaceEventSessionNotFoundForBetAnswersError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.answers.race_event_session_not_found",
    ),
    TestingEventSessionNotFoundForBetAnswersError: ErrorCatalogEntry(
        status_code=404,
        error_code="bets.answers.testing_event_session_not_found",
    ),
    BetAnswersNotOpenError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.answers.not_open",
    ),
    BetAnswersClosedError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.answers.closed",
    ),
    BetAlreadySubmittedError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.answers.already_submitted",
    ),
    BetAnswerQuestionNotFoundError: ErrorCatalogEntry(
        status_code=422,
        error_code="bets.answers.question_not_found",
    ),
    BetRequiredAnswerMissingError: ErrorCatalogEntry(
        status_code=422,
        error_code="bets.answers.required_answer_missing",
    ),
    BetModificationLimitReachedError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.answers.modification_limit_reached",
    ),
    BetAnswerRelationViolationError: ErrorCatalogEntry(
        status_code=422,
        error_code="bets.answers.relation_violation",
    ),
}
