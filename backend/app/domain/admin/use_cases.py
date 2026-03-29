from app.domain.admin.errors import (
    ActiveSeasonAlreadyExistsError,
    SeasonAlreadyExistsError,
)
from app.domain.admin.ports import AdminSeasonRepository


class PublishResults:
    def execute(self, user_id: int) -> dict:
        return {"published_by": user_id}


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
