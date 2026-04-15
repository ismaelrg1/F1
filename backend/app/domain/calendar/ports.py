from typing import Protocol

from app.domain.calendar.models import CalendarEvent


class CalendarRepository(Protocol):
    def list_events(self, *, season_year: int | None = None) -> list[CalendarEvent]:
        ...