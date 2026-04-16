from typing import Protocol

from app.domain.admin.race_events.models import (
    AdminRaceEvent,
    AdminRaceEventCircuit,
    AdminRaceEventSeason,
    AdminRaceEventSessionWrite,
)


class AdminRaceEventRepository(Protocol):
    def get_by_id(self, race_event_id: int) -> AdminRaceEvent | None:
        ...

    def get_season_by_year(self, year: int) -> AdminRaceEventSeason | None:
        ...

    def get_circuit_by_code(self, code: str) -> AdminRaceEventCircuit | None:
        ...

    def get_by_season_and_round(self, *, season_id: int, round_number: int) -> AdminRaceEvent | None:
        ...

    def list_race_events(self, *, season_year: int | None = None) -> list[AdminRaceEvent]:
        ...

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        round_number: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminRaceEventSessionWrite],
    ) -> AdminRaceEvent:
        ...

    def update(
        self,
        *,
        race_event_id: int,
        season_id: int,
        circuit_id: int,
        round_number: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminRaceEventSessionWrite],
    ) -> AdminRaceEvent:
        ...