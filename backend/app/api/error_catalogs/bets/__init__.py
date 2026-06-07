from app.api.error_catalogs.bets.answers import BET_ANSWERS_ERROR_MAP
from app.api.error_catalogs.bets.generic import BET_GENERIC_ERROR_MAP
from app.api.error_catalogs.bets.powerups import BET_POWERUPS_ERROR_MAP
from app.api.error_catalogs.bets.questions import BET_QUESTIONS_ERROR_MAP
from app.api.error_catalogs.bets.results import BET_RESULTS_ERROR_MAP


BETS_ERROR_MAP = {
    **BET_GENERIC_ERROR_MAP,
    **BET_QUESTIONS_ERROR_MAP,
    **BET_ANSWERS_ERROR_MAP,
    **BET_RESULTS_ERROR_MAP,
    **BET_POWERUPS_ERROR_MAP,
}


__all__ = ["BETS_ERROR_MAP"]