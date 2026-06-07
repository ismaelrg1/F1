from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.bets.powerups.errors import (
    PowerUpsBetContextNotFoundError,
    PowerUpsRaceEventNotFoundError,
    PowerUpsRaceEventSessionNotFoundError,
    PowerUpsSeasonNotFoundError,
    PowerUpsTestingEventNotFoundError,
    PowerUpsTestingEventSessionNotFoundError,
)
from app.domain.bets.errors import (
    BetPowerUpAlreadyUsedError,
    BetPowerUpDisabledError,
    BetPowerUpNotAssignedError,
    BetPowerUpPenaltyLimitReachedError,
    BetPowerUpRestrictedError,
    BetPowerUpsCannotBeUsedAfterSubmitError,
    BetPowerUpTargetNotAllowedError,
    BetPowerUpTargetRequiredError,
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

    BetPowerUpsCannotBeUsedAfterSubmitError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.powerups.cannot_be_used_after_submit",
    ),
    BetPowerUpDisabledError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.powerups.disabled",
    ),
    BetPowerUpNotAssignedError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.powerups.not_assigned",
    ),
    BetPowerUpAlreadyUsedError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.powerups.already_used",
    ),
    BetPowerUpRestrictedError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.powerups.restricted",
    ),
    BetPowerUpTargetRequiredError: ErrorCatalogEntry(
        status_code=422,
        error_code="bets.powerups.target_required",
    ),
    BetPowerUpTargetNotAllowedError: ErrorCatalogEntry(
        status_code=422,
        error_code="bets.powerups.target_not_allowed",
    ),
    BetPowerUpPenaltyLimitReachedError: ErrorCatalogEntry(
        status_code=409,
        error_code="bets.powerups.penalty_limit_reached",
    ),
}
