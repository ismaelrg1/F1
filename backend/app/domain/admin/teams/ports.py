from typing import Protocol

from app.db.competition import Season, SeasonTeam, TeamF1


class AdminTeamRepository(Protocol):
    def get_by_code(self, code: str) -> TeamF1 | None:
        ...

    def create(self, *, code: str, name: str) -> TeamF1:
        ...

    def get_season_by_year(self, year: int) -> Season | None:
        ...

    def get_season_team(self, *, season_id: int, team_id: int) -> SeasonTeam | None:
        ...

    def create_season_team(self, *, season_id: int, team_id: int, is_active: bool) -> SeasonTeam:
        ...