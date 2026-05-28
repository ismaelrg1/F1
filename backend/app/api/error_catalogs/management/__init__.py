from app.api.error_catalogs.management.group import MANAGEMENT_GROUP_ERROR_MAP
from app.api.error_catalogs.management.official_results import OFFICIAL_RESULTS_ERROR_MAP
from app.api.error_catalogs.management.result_publications import RESULT_PUBLICATIONS_ERROR_MAP

MANAGEMENT_ERROR_MAP = {
    **MANAGEMENT_GROUP_ERROR_MAP,
    **OFFICIAL_RESULTS_ERROR_MAP,
    **RESULT_PUBLICATIONS_ERROR_MAP,
}

__all__ = ["MANAGEMENT_ERROR_MAP"]
