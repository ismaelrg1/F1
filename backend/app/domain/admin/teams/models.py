from dataclasses import dataclass


@dataclass(frozen=True)
class AdminTeam:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class AdminTeamSeason:
    id: int
    year: int


@dataclass(frozen=True)
class AdminSeasonTeam:
    season_year: int
    team_code: str
    is_active: bool