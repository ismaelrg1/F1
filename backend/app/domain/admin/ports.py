from typing import Protocol

from app.db.competition import Season

class AdminSeasonRepository(Protocol):
    def get_by_year(self, year: int) -> Season | None:
        ...

    def get_active_season(self) -> Season | None:
        ...

    def create(self, *, year: int, is_active: bool) -> Season:
        ...