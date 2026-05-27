from app.domain.management.calendar.models import ManagementCalendarEvent
from app.domain.management.calendar.ports import ManagementCalendarRepository


class GetManagementCalendar:
    def __init__(self, repository: ManagementCalendarRepository):
        self._repository = repository

    def execute(
        self,
        *,
        season_year: int | None,
        group_id: int,
    ) -> list[ManagementCalendarEvent]:
        return self._repository.list_events(
            season_year=season_year,
            group_id=group_id,
        )