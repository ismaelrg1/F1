from dataclasses import dataclass


@dataclass(frozen=True)
class AdminEngine:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class AdminEngineSeason:
    id: int
    year: int


@dataclass(frozen=True)
class AdminSeasonEngine:
    season_year: int
    engine_code: str
    is_active: bool