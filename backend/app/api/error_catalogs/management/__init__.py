from app.api.error_catalogs.management.official_results import OFFICIAL_RESULTS_ERROR_MAP

MANAGEMENT_ERROR_MAP = {
    **OFFICIAL_RESULTS_ERROR_MAP,
}

__all__ = ["MANAGEMENT_ERROR_MAP"]