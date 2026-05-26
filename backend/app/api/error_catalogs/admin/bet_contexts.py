from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.admin.bet_contexts.errors import (
    BetContextGenerationGroupNotFoundError,
    BetContextGenerationSeasonNotFoundError,
    BetContextGenerationForbiddenGroupError,
    BetContextGenerationGroupScopeRequiredError,
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
    BetContextGenerationGroupScopeRequiredError: ErrorCatalogEntry(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="admin.bet_context_generation_group_scope_required",
    ),
    BetContextGenerationForbiddenGroupError: ErrorCatalogEntry(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="admin.bet_context_generation_forbidden_group",
    ),
}
