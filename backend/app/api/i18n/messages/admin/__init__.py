from app.api.i18n.messages.admin.circuits import MESSAGES_ADMIN_CIRCUITS
from app.api.i18n.messages.admin.countries import MESSAGES_ADMIN_COUNTRIES
from app.api.i18n.messages.admin.drivers import MESSAGES_ADMIN_DRIVERS
from app.api.i18n.messages.admin.engines import MESSAGES_ADMIN_ENGINES
from app.api.i18n.messages.admin.race_events import MESSAGES_ADMIN_RACE_EVENTS
from app.api.i18n.messages.admin.seasons import MESSAGES_ADMIN_SEASONS
from app.api.i18n.messages.admin.teams import MESSAGES_ADMIN_TEAMS
from app.api.i18n.messages.admin.testing_events import MESSAGES_ADMIN_TESTING_EVENTS
from app.api.i18n.messages.admin.bet_contexts import MESSAGES_ADMIN_BET_CONTEXTS
from app.api.i18n.messages.admin.official_results import MESSAGES_ADMIN_OFFICIAL_RESULTS


MESSAGES_ADMIN = {
    **MESSAGES_ADMIN_SEASONS,
    **MESSAGES_ADMIN_COUNTRIES,
    **MESSAGES_ADMIN_CIRCUITS,
    **MESSAGES_ADMIN_TESTING_EVENTS,
    **MESSAGES_ADMIN_RACE_EVENTS,
    **MESSAGES_ADMIN_DRIVERS,
    **MESSAGES_ADMIN_TEAMS,
    **MESSAGES_ADMIN_ENGINES,
    **MESSAGES_ADMIN_BET_CONTEXTS,
    **MESSAGES_ADMIN_OFFICIAL_RESULTS,
}

__all__ = ["MESSAGES_ADMIN"]