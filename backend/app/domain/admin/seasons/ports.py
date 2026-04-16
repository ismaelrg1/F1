from typing import Protocol

from app.domain.admin.seasons.models import AdminSeason


class AdminSeasonRepository(Protocol):
    def get_by_year(self, year: int) -> AdminSeason | None:
        ...

    def get_active_season(self) -> AdminSeason | None:
        ...

    def create(self, *, year: int, is_active: bool) -> AdminSeason:
        ...
