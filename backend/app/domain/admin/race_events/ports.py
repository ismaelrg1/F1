from typing import Protocol

from app.db.competition import Circuit, RaceEvent, Season


class AdminRaceEventRepository(Protocol):
    def get_by_id(self, race_event_id: int) -> RaceEvent | None:
        ...

    def get_season_by_year(self, year: int) -> Season | None:
        ...

    def get_circuit_by_code(self, code: str) -> Circuit | None:
        ...

    def get_by_season_and_round(self, *, season_id: int, round_number: int) -> RaceEvent | None:
        ...

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        round_number: int,
        name: str,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ) -> RaceEvent:
        ...

    def update(
        self,
        *,
        race_event: RaceEvent,
        season_id: int,
        circuit_id: int,
        round_number: int,
        name: str,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ) -> RaceEvent:
        ...
