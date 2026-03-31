from typing import Protocol

from app.db.competition import RaceEvent, TestingEvent


class HomeRepository(Protocol):
    def get_next_event_for_active_season(self) -> RaceEvent | TestingEvent | None:
        ...
