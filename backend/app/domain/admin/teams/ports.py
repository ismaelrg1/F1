from typing import Protocol

from app.domain.admin.teams.models import (
    AdminSeasonTeam,
    AdminTeam,
    AdminTeamSeason,
)


class AdminTeamRepository(Protocol):
    def get_by_code(self, code: str) -> AdminTeam | None:
        ...

    def create(self, *, code: str, name: str, color: str) -> AdminTeam:
        ...

    def get_season_by_year(self, year: int) -> AdminTeamSeason | None:
        ...

    def get_season_team(self, *, season_id: int, team_id: int) -> AdminSeasonTeam | None:
        ...

    def create_season_team(self, *, season_id: int, team_id: int, is_active: bool) -> AdminSeasonTeam:
        ...
