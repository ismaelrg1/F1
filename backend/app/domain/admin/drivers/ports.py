from typing import Protocol

from app.domain.admin.drivers.models import (
    AdminDriver,
    AdminDriverSeason,
    AdminSeasonDriver,
)


class AdminDriverRepository(Protocol):
    def get_by_code(self, code: str) -> AdminDriver | None:
        ...

    def create(self, *, code: str, name: str, nationality_country_id: int | None = None) -> AdminDriver:
        ...

    def get_season_by_year(self, year: int) -> AdminDriverSeason | None:
        ...

    def get_season_driver(self, *, season_id: int, driver_id: int) -> AdminSeasonDriver | None:
        ...

    def create_season_driver(self, *, season_id: int, driver_id: int, status) -> AdminSeasonDriver:
        ...