from typing import Protocol

from app.domain.admin.seasons.models import AdminSeason


class AdminSeasonRepository(Protocol):
    def get_by_year(self, year: int) -> AdminSeason | None:
        ...

    def get_active_season(self) -> AdminSeason | None:
        ...

    def create(self, *, year: int, is_active: bool) -> AdminSeason:
        ...
    
    def list_seasons(self, *, is_active: bool | None = None) -> list[AdminSeason]:
        ...

    def get_by_id(self, season_id: int) -> AdminSeason | None:
        ...

    def update_is_active(self, *, season_id: int, is_active: bool) -> AdminSeason:
        ...

    def deactivate_other_seasons(self, *, except_season_id: int) -> None:
        ...
