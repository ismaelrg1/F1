from app.domain.admin.seasons.errors import (
    ActiveSeasonAlreadyExistsError,
    SeasonAlreadyExistsError,
    SeasonNotFoundError,
)
from app.domain.admin.seasons.models import AdminSeason
from app.domain.admin.seasons.ports import AdminSeasonRepository


class CreateSeason:
    def __init__(self, repository: AdminSeasonRepository):
        self._repository = repository

    def execute(self, *, year: int, is_active: bool) -> AdminSeason:
        existing = self._repository.get_by_year(year)
        if existing is not None:
            raise SeasonAlreadyExistsError(year=year)

        if is_active:
            active = self._repository.get_active_season()
            if active is not None:
                raise ActiveSeasonAlreadyExistsError(active_year=active.year)

        return self._repository.create(year=year, is_active=is_active)


class ListSeasons:
    def __init__(self, repository: AdminSeasonRepository):
        self._repository = repository

    def execute(self, is_active: bool | None = None) -> list[AdminSeason]:
        return self._repository.list_seasons(is_active=is_active)
    
class UpdateSeasonIsActive:
    def __init__(self, repository: AdminSeasonRepository):
        self._repository = repository

    def execute(self, *, season_id: int, is_active: bool) -> AdminSeason | None:
        season = self._repository.get_by_id(season_id)
        if season is None:
            raise SeasonNotFoundError(season_id=season_id)
        
        if is_active:
            self._repository.deactivate_other_seasons(except_season_id=season_id)
        
        return self._repository.update_is_active(
            season_id=season_id,
            is_active=is_active,
        )

