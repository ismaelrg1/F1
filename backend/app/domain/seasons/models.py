from dataclasses import dataclass


@dataclass(frozen=True)
class SeasonSummary:
    id: int
    year: int
    is_active: bool


@dataclass(frozen=True)
class SeasonRosterEntry:
    code: str
    name: str


@dataclass(frozen=True)
class SeasonRoster:
    season_id: int
    drivers: list[SeasonRosterEntry]
    teams: list[SeasonRosterEntry]
    engines: list[SeasonRosterEntry]
