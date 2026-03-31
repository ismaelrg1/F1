from typing import Protocol

from app.db.competition import Driver, Season, SeasonDriver


class AdminDriverRepository(Protocol):
    def get_by_code(self, code: str) -> Driver | None:
        ...

    def create(self, *, code: str, name: str) -> Driver:
        ...

    def get_season_by_year(self, year: int) -> Season | None:
        ...

    def get_season_driver(self, *, season_id: int, driver_id: int) -> SeasonDriver | None:
        ...

    def create_season_driver(self, *, season_id: int, driver_id: int, status) -> SeasonDriver:
        ...