from __future__ import annotations

from datetime import UTC, datetime

from app.domain.calendar.models import CalendarEvent, CalendarEventResult
from app.domain.calendar.ports import CalendarRepository


class GetCalendar:
    def __init__(self, repository: CalendarRepository):
        self._repository = repository

    @staticmethod
    def _event_sort_datetime(event: CalendarEvent) -> datetime:
        return event.event_start or event.scheduled_event_start or datetime.max.replace(tzinfo=UTC)

    def execute(self, *, season_year: int | None = None) -> list[CalendarEventResult]:
        events = self._repository.list_events(season_year=season_year)

        now = datetime.now(UTC)
        upcoming_candidates = [
            event
            for event in events
            if (event.event_start or event.scheduled_event_start) is not None
            and (event.event_start or event.scheduled_event_start) >= now
            and event.status in {"SCHEDULED", "POSTPONED"}
        ]

        up_next_id: int | None = None
        if upcoming_candidates:
            next_event = min(
                upcoming_candidates,
                key=lambda event: (
                    self._event_sort_datetime(event),
                    0 if event.kind == "TESTING" else 1,
                    event.round_number or 0,
                    event.id,
                ),
            )
            up_next_id = next_event.id

        sorted_items = sorted(
            events,
            key=lambda event: (
                0 if event.kind == "TESTING" else 1,
                self._event_sort_datetime(event),
                event.round_number or 0,
                event.id,
            ),
        )

        return [
            CalendarEventResult(
                event=event,
                is_up_next=event.id == up_next_id,
            )
            for event in sorted_items
        ]
