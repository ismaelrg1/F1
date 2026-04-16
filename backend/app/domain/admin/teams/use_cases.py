from app.domain.admin.teams.errors import (
    SeasonNotFoundForSeasonTeamError,
    SeasonTeamAlreadyExistsError,
    TeamAlreadyExistsError,
    TeamNotFoundForSeasonTeamError,
)
from app.domain.admin.teams.ports import AdminTeamRepository


class CreateTeam:
    def __init__(self, repository: AdminTeamRepository):
        self._repository = repository

    def execute(self, *, code: str, name: str):
        normalized_code = code.strip().upper()

        existing = self._repository.get_by_code(normalized_code)
        if existing is not None:
            raise TeamAlreadyExistsError(code=normalized_code)

        return self._repository.create(
            code=normalized_code,
            name=name.strip(),
        )


class CreateSeasonTeam:
    def __init__(self, repository: AdminTeamRepository):
        self._repository = repository

    def execute(self, *, season_year: int, team_code: str, is_active: bool):
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForSeasonTeamError(season_year=season_year)

        normalized_team_code = team_code.strip().upper()
        team = self._repository.get_by_code(normalized_team_code)
        if team is None:
            raise TeamNotFoundForSeasonTeamError(team_code=normalized_team_code)

        existing = self._repository.get_season_team(
            season_id=season.id,
            team_id=team.id,
        )
        if existing is not None:
            raise SeasonTeamAlreadyExistsError(
                season_year=season.year,
                team_code=normalized_team_code,
            )

        return self._repository.create_season_team(
            season_id=season.id,
            team_id=team.id,
            is_active=is_active,
        )