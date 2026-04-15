from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyCalendarRepository
from app.api.deps import get_current_user

from app.db.auth import User
from app.db.session import get_db
from app.domain.calendar import GetCalendar

from app.models.calendar import (
    CalendarEventRead,
    CalendarRaceSessionRead,
    CalendarResponse,
    CalendarTestingSessionRead,
)

router = APIRouter()

@router.get(
    "/calendar",
    response_model=CalendarResponse,
)
def get_calendar(
    season_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CalendarResponse:
    repository = SqlAlchemyCalendarRepository(db)
    use_case = GetCalendar(repository)
    results = use_case.execute(season_year=season_year)

    items = [
        CalendarEventRead(
            kind=result.event.kind,
            public_id=result.event.public_id,
            season_year=result.event.season_year,
            round_number=result.event.round_number,
            name=result.event.name,
            circuit_code=result.event.circuit_code,
            circuit_name=result.event.circuit_name,
            country_name=result.event.country_name,
            event_start=result.event.event_start,
            event_end=result.event.event_end,
            scheduled_event_start=result.event.scheduled_event_start,
            scheduled_event_end=result.event.scheduled_event_end,
            status=result.event.status,
            status_reason=result.event.status_reason,
            is_up_next=result.is_up_next,
            testing_sessions=[
                CalendarTestingSessionRead(
                    public_id=session.public_id,
                    session_order=session.session_order,
                    name=session.name,
                    start_datetime=session.start_datetime,
                    end_datetime=session.end_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    scheduled_end_datetime=session.scheduled_end_datetime,
                )
                for session in result.event.testing_sessions
            ],
            race_sessions=[
                CalendarRaceSessionRead(
                    public_id=session.public_id,
                    session_type=session.session_type,
                    start_datetime=session.start_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    lock_cutoff=session.lock_cutoff,
                    scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                    status=session.status,
                    status_reason=session.status_reason,
                )
                for session in result.event.race_sessions
            ],
        )
        for result in results
    ]

    return CalendarResponse(items=items)
