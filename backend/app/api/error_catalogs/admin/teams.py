from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry

from app.domain.admin.teams.errors import (
    SeasonNotFoundForSeasonTeamError,
    SeasonTeamAlreadyExistsError,
    TeamAlreadyExistsError,
    TeamNotFoundForSeasonTeamError,
)

ADMIN_TEAM_ERROR_MAP = {
    TeamAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.team_already_exists",
    ),
    SeasonNotFoundForSeasonTeamError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.season_not_found_for_season_team",
    ),
    TeamNotFoundForSeasonTeamError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="admin.team_not_found_for_season_team",
    ),
    SeasonTeamAlreadyExistsError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="admin.season_team_already_exists",
    ),
}