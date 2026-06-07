from app.api.i18n.messages.bets.answers import MESSAGES_BET_ANSWERS
from app.api.i18n.messages.bets.generic import MESSAGES_BET_GENERIC
from app.api.i18n.messages.bets.powerups import MESSAGES_BET_POWERUPS
from app.api.i18n.messages.bets.questions import MESSAGES_BET_QUESTIONS
from app.api.i18n.messages.bets.results import MESSAGES_BET_RESULTS


MESSAGES_BETS = {
    "en": {
        **MESSAGES_BET_GENERIC["en"],
        **MESSAGES_BET_QUESTIONS["en"],
        **MESSAGES_BET_ANSWERS["en"],
        **MESSAGES_BET_RESULTS["en"],
        **MESSAGES_BET_POWERUPS["en"],
    },
    "es": {
        **MESSAGES_BET_GENERIC["es"],
        **MESSAGES_BET_QUESTIONS["es"],
        **MESSAGES_BET_ANSWERS["es"],
        **MESSAGES_BET_RESULTS["es"],
        **MESSAGES_BET_POWERUPS["es"],
    },
}


__all__ = ["MESSAGES_BETS"]