from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.ranking.errors import SeasonNotFoundForRankingError


RANKING_ERROR_MAP = {
    SeasonNotFoundForRankingError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="ranking.season_not_found",
    ),
}