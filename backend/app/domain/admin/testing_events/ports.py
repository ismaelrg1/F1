from typing import Protocol

from app.db.competition import Circuit, Season, TestingEvent
from app.db.enums import TestingEventStatus


class AdminTestingEventRepository(Protocol):
    def get_by_id(self, testing_event_id: int) -> TestingEvent | None:
        ...

    def get_season_by_year(self, year: int) -> Season | None:
        ...

    def get_circuit_by_code(self, code: str) -> Circuit | None:
        ...

    def get_by_season_and_name(self, *, season_id: int, name: str) -> TestingEvent | None:
        ...

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        name: str,
        source_provider,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: TestingEventStatus | None,
        status_reason: str | None,
        sessions: list[dict],
    ) -> TestingEvent:
        ...

    def update(
        self,
        *,
        testing_event: TestingEvent,
        season_id: int,
        circuit_id: int,
        name: str,
        source_provider,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ) -> TestingEvent:
        ...
