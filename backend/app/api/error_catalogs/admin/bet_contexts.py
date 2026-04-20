from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.admin.bet_contexts.errors import (
    BetContextGenerationGroupNotFoundError,
    BetContextGenerationSeasonNotFoundError,
)

ADMIN_BET_CONTEXT_ERROR_MAP = {
    BetContextGenerationSeasonNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.bet_context_generation_season_not_found",
    ),
    BetContextGenerationGroupNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.bet_context_generation_group_not_found",
    ),
}
