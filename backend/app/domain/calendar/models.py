from dataclasses import dataclass

from app.db.competition import RaceEvent, TestingEvent

@dataclass(frozen=True)
class CalendarEventResult:
    kind: str
    event: RaceEvent | TestingEvent
    is_up_next: bool
