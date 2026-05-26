from app.api.error_catalogs.admin.circuits import ADMIN_CIRCUIT_ERROR_MAP
from app.api.error_catalogs.admin.countries import ADMIN_COUNTRY_ERROR_MAP
from app.api.error_catalogs.admin.drivers import ADMIN_DRIVER_ERROR_MAP
from app.api.error_catalogs.admin.engines import ADMIN_ENGINE_ERROR_MAP
from app.api.error_catalogs.admin.race_events import ADMIN_RACE_EVENT_ERROR_MAP
from app.api.error_catalogs.admin.seasons import ADMIN_SEASON_ERROR_MAP
from app.api.error_catalogs.admin.teams import ADMIN_TEAM_ERROR_MAP
from app.api.error_catalogs.admin.testing_events import ADMIN_TESTING_EVENT_ERROR_MAP
from app.api.error_catalogs.admin.bet_contexts import ADMIN_BET_CONTEXT_ERROR_MAP
from app.api.error_catalogs.admin.official_results import ADMIN_OFFICIAL_RESULTS_ERROR_MAP

ADMIN_ERROR_MAP = {
    **ADMIN_SEASON_ERROR_MAP,
    **ADMIN_COUNTRY_ERROR_MAP,
    **ADMIN_CIRCUIT_ERROR_MAP,
    **ADMIN_TESTING_EVENT_ERROR_MAP,
    **ADMIN_RACE_EVENT_ERROR_MAP,
    **ADMIN_DRIVER_ERROR_MAP,
    **ADMIN_TEAM_ERROR_MAP,
    **ADMIN_ENGINE_ERROR_MAP,
    **ADMIN_BET_CONTEXT_ERROR_MAP,
    **ADMIN_OFFICIAL_RESULTS_ERROR_MAP,
}

__all__ = ["ADMIN_ERROR_MAP"]