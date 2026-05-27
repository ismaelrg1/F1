from app.api.error_catalogs.access import ACCESS_ERROR_MAP
from app.api.error_catalogs.auth import AUTH_ERROR_MAP
from app.api.error_catalogs.admin import ADMIN_ERROR_MAP
from app.api.error_catalogs.bets import BETS_ERROR_MAP
from app.api.error_catalogs.ranking import RANKING_ERROR_MAP
from app.api.error_catalogs.management import MANAGEMENT_ERROR_MAP
from app.api.error_catalogs.base import ErrorCatalogEntry

__all__ = [
    "ACCESS_ERROR_MAP",

    "AUTH_ERROR_MAP",

    "ADMIN_ERROR_MAP",
    
    "BETS_ERROR_MAP",

    "RANKING_ERROR_MAP",

    "MANAGEMENT_ERROR_MAP",
    
    "ErrorCatalogEntry",
]
