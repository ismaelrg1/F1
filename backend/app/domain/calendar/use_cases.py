from __future__ import annotations

from datetime import UTC, datetime

from app.db.competition import RaceEvent, TestingEvent
from app.domain.calendar.ports import CalendarRepository

from app.domain.calendar.models import CalendarEventResult


class GetCalendar:
    def __init__(self, repository: CalendarRepository):
        self._repository = repository

    @staticmethod
    def _event_sort_datetime(event: RaceEvent | TestingEvent) -> datetime:
        return event.event_start or event.scheduled_event_start or datetime.max.replace(tzinfo=UTC)

    def execute(self, *, season_year: int | None = None) -> list[CalendarEventResult]:
        testing_events = self._repository.list_testing_events(season_year=season_year)
        race_events = self._repository.list_race_events(season_year=season_year)

        raw_items: list[tuple[str, RaceEvent | TestingEvent]] = [
            *[("TESTING", event) for event in testing_events],
            *[("RACE", event) for event in race_events],
        ]

        now = datetime.now(UTC)
        upcoming_candidates = [
            (kind, event)
            for kind, event in raw_items
            if (event.event_start or event.scheduled_event_start) is not None
            and (event.event_start or event.scheduled_event_start) >= now
            and event.status.value in {"SCHEDULED", "POSTPONED"}
        ]

        up_next_key: tuple[str, int] | None = None
        if upcoming_candidates:
            next_kind, next_event = min(
                upcoming_candidates,
                key=lambda item: (
                    self._event_sort_datetime(item[1]),
                    getattr(item[1], "round_number", 0) or 0,
                    item[1].id,
                ),
            )
            up_next_key = (next_kind, next_event.id)

        sorted_items = sorted(
            raw_items,
            key=lambda item: (
                0 if item[0] == "TESTING" else 1,
                self._event_sort_datetime(item[1]),
                getattr(item[1], "round_number", 0) or 0,
                item[1].id,
            ),
        )

        return [
            CalendarEventResult(
                kind=kind,
                event=event,
                is_up_next=(kind, event.id) == up_next_key,
            )
            for kind, event in sorted_items
        ]
