from typing import Protocol, Any

from app.domain.admin.fastf1.models import (
    FastF1RaceEventPreview,
    FastF1TestingEventPreview,
)


class AdminFastF1Repository(Protocol):
    def list_race_event_previews(self, year: int) -> list[FastF1RaceEventPreview]:
        ...

    def list_testing_event_previews(self, year: int) -> list[FastF1TestingEventPreview]:
        ...