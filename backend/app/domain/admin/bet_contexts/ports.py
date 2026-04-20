from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AdminBetContextRaceEvent:
    id: int
    season_id: int
    name: str


@dataclass(frozen=True)
class AdminBetContextTestingEvent:
    id: int
    season_id: int
    name: str


class AdminBetContextRepository(Protocol):
    def season_exists(self, *, season_id: int) -> bool:
        ...

    def group_exists(self, *, group_id: int) -> bool:
        ...

    def list_group_ids(self, *, group_id: int | None) -> list[int]:
        ...

    def list_race_events_for_season(self, *, season_id: int) -> list[AdminBetContextRaceEvent]:
        ...

    def list_testing_events_for_season(self, *, season_id: int) -> list[AdminBetContextTestingEvent]:
        ...

    def ensure_season_context(
        self,
        *,
        group_id: int,
        season_id: int,
        label: str,
    ) -> bool:
        ...

    def ensure_race_event_context(
        self,
        *,
        group_id: int,
        season_id: int,
        race_event_id: int,
        label: str,
    ) -> bool:
        ...

    def ensure_testing_event_context(
        self,
        *,
        group_id: int,
        season_id: int,
        testing_event_id: int,
        label: str,
    ) -> bool:
        ...