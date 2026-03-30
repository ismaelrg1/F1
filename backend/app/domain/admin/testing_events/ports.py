from typing import Protocol

from app.db.competition import Circuit, Season, TestingEvent


class AdminTestingEventRepository(Protocol):
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
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status_reason: str | None,
        sessions: list[dict],
    ) -> TestingEvent:
        ...
