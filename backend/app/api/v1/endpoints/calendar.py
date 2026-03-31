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

    items: list[CalendarEventRead] = []
    for result in results:
        event = result.event
        if result.kind == "TESTING":
            items.append(
                CalendarEventRead(
                    kind="TESTING",
                    public_id=event.public_id,
                    season_year=event.season.year,
                    round_number=None,
                    name=event.name,
                    circuit_code=event.circuit.code,
                    circuit_name=event.circuit.name,
                    country_name=event.circuit.country.name,
                    event_start=event.event_start,
                    event_end=event.event_end,
                    scheduled_event_start=event.scheduled_event_start,
                    scheduled_event_end=event.scheduled_event_end,
                    status=event.status.value,
                    status_reason=event.status_reason,
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
                        for session in sorted(event.sessions, key=lambda s: s.session_order)
                    ],
                    race_sessions=[],
                )
            )
        else:
            items.append(
                CalendarEventRead(
                    kind="RACE",
                    public_id=event.public_id,
                    season_year=event.season.year,
                    round_number=event.round_number,
                    name=event.name,
                    circuit_code=event.circuit.code,
                    circuit_name=event.circuit.name,
                    country_name=event.circuit.country.name,
                    event_start=event.event_start,
                    event_end=event.event_end,
                    scheduled_event_start=event.scheduled_event_start,
                    scheduled_event_end=event.scheduled_event_end,
                    status=event.status.value,
                    status_reason=event.status_reason,
                    is_up_next=result.is_up_next,
                    testing_sessions=[],
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
                        for session in sorted(
                            event.event_sessions,
                            key=lambda s: (s.scheduled_start_datetime or s.start_datetime, s.id),
                        )
                    ],
                )
            )

    return CalendarResponse(items=items)
