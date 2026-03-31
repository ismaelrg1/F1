from typing import Protocol

from app.db.competition import RaceEvent, TestingEvent


class CalendarRepository(Protocol):
    def list_testing_events(self, *, season_year: int | None = None) -> list[TestingEvent]:
        ...

    def list_race_events(self, *, season_year: int | None = None) -> list[RaceEvent]:
        ...
