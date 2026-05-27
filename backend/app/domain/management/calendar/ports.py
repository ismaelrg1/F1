from typing import Protocol

from app.domain.management.calendar.models import ManagementCalendarEvent


class ManagementCalendarRepository(Protocol):
    def list_events(
        self,
        *,
        season_year: int | None,
        group_id: int,
    ) -> list[ManagementCalendarEvent]:
        ...