from app.api.i18n.messages.admin.bet_contexts import MESSAGES_ADMIN_BET_CONTEXTS
from app.api.i18n.messages.admin.circuits import MESSAGES_ADMIN_CIRCUITS
from app.api.i18n.messages.admin.countries import MESSAGES_ADMIN_COUNTRIES
from app.api.i18n.messages.admin.drivers import MESSAGES_ADMIN_DRIVERS
from app.api.i18n.messages.admin.engines import MESSAGES_ADMIN_ENGINES
from app.api.i18n.messages.admin.race_events import MESSAGES_ADMIN_RACE_EVENTS
from app.api.i18n.messages.admin.seasons import MESSAGES_ADMIN_SEASONS
from app.api.i18n.messages.admin.teams import MESSAGES_ADMIN_TEAMS
from app.api.i18n.messages.admin.testing_events import MESSAGES_ADMIN_TESTING_EVENTS

MESSAGES_ADMIN = {
    "en": {
        **MESSAGES_ADMIN_SEASONS["en"],
        **MESSAGES_ADMIN_COUNTRIES["en"],
        **MESSAGES_ADMIN_CIRCUITS["en"],
        **MESSAGES_ADMIN_TESTING_EVENTS["en"],
        **MESSAGES_ADMIN_RACE_EVENTS["en"],
        **MESSAGES_ADMIN_DRIVERS["en"],
        **MESSAGES_ADMIN_TEAMS["en"],
        **MESSAGES_ADMIN_ENGINES["en"],
        **MESSAGES_ADMIN_BET_CONTEXTS["en"],
    },
    "es": {
        **MESSAGES_ADMIN_SEASONS["es"],
        **MESSAGES_ADMIN_COUNTRIES["es"],
        **MESSAGES_ADMIN_CIRCUITS["es"],
        **MESSAGES_ADMIN_TESTING_EVENTS["es"],
        **MESSAGES_ADMIN_RACE_EVENTS["es"],
        **MESSAGES_ADMIN_DRIVERS["es"],
        **MESSAGES_ADMIN_TEAMS["es"],
        **MESSAGES_ADMIN_ENGINES["es"],
        **MESSAGES_ADMIN_BET_CONTEXTS["es"],
    },
}

__all__ = ["MESSAGES_ADMIN"]
