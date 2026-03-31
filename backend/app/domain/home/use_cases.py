from __future__ import annotations

from dataclasses import dataclass

from app.db.competition import RaceEvent, TestingEvent
from app.domain.home.ports import HomeRepository


@dataclass(frozen=True)
class HomeEventResult:
    kind: str
    event: RaceEvent | TestingEvent


class GetHome:
    def __init__(self, repository: HomeRepository):
        self._repository = repository

    def execute(self) -> HomeEventResult | None:
        next_event = self._repository.get_next_event_for_active_season()
        if next_event is None:
            return None

        kind = "RACE" if isinstance(next_event, RaceEvent) else "TESTING"
        return HomeEventResult(kind=kind, event=next_event)
