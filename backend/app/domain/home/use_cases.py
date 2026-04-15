from __future__ import annotations

from app.domain.home.ports import HomeRepository
from app.domain.home.models import HomeEventResult

class GetHome:
    def __init__(self, repository: HomeRepository):
        self._repository = repository

    def execute(self) -> HomeEventResult | None:
        return self._repository.get_next_event_for_active_season()
