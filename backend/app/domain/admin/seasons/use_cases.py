from app.domain.admin.seasons.errors import (
    ActiveSeasonAlreadyExistsError,
    SeasonAlreadyExistsError,
)
from app.domain.admin.seasons.ports import AdminSeasonRepository


class CreateSeason:
    def __init__(self, repository: AdminSeasonRepository):
        self._repository = repository

    def execute(self, *, year: int, is_active: bool):
        existing = self._repository.get_by_year(year)
        if existing is not None:
            raise SeasonAlreadyExistsError(year=year)

        if is_active:
            active = self._repository.get_active_season()
            if active is not None:
                raise ActiveSeasonAlreadyExistsError(active_year=active.year)

        return self._repository.create(year=year, is_active=is_active)
