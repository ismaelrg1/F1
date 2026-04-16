from __future__ import annotations

from typing import Protocol

from app.domain.admin.testing_events.models import (
    AdminTestingEvent,
    AdminTestingEventCircuit,
    AdminTestingEventSeason,
    AdminTestingEventSessionWrite,
)


class AdminTestingEventRepository(Protocol):
    def get_by_id(self, testing_event_id: int) -> AdminTestingEvent | None:
        ...

    def get_season_by_year(self, year: int) -> AdminTestingEventSeason | None:
        ...

    def get_circuit_by_code(self, code: str) -> AdminTestingEventCircuit | None:
        ...

    def get_by_season_and_name(self, *, season_id: int, name: str) -> AdminTestingEvent | None:
        ...

    def list_testing_events(self, *, season_year: int | None = None) -> list[AdminTestingEvent]:
        ...

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminTestingEventSessionWrite],
    ) -> AdminTestingEvent:
        ...

    def update(
        self,
        *,
        testing_event_id: int,
        season_id: int,
        circuit_id: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminTestingEventSessionWrite],
    ) -> AdminTestingEvent:
        ...
