from typing import Protocol

from app.domain.home.models import HomeEventResult

class HomeRepository(Protocol):
    def get_next_event_for_active_season(self) -> HomeEventResult | None:
        ...
