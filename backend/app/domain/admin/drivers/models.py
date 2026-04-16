from dataclasses import dataclass


@dataclass(frozen=True)
class AdminDriver:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class AdminDriverSeason:
    id: int
    year: int


@dataclass(frozen=True)
class AdminSeasonDriver:
    season_year: int
    driver_code: str
    status: str