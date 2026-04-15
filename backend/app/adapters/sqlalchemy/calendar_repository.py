from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.competition import ( 
    Circuit,
    RaceEvent,
    Season,
    TestingEvent,
)

from app.domain.calendar.models import (
    CalendarEvent,
    CalendarRaceSession,
    CalendarTestingSession,
)

from app.domain.calendar.ports import CalendarRepository

class SqlAlchemyCalendarRepository(CalendarRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_events(self, *, season_year: int | None = None) -> list[CalendarEvent]:
        testing_events = self._session.execute(
            self._testing_stmt(season_year=season_year)
        ).scalars().unique().all()

        race_events = self._session.execute(
            self._race_stmt(season_year=season_year)
        ).scalars().unique().all()

        items: list[CalendarEvent] = []

        for event in testing_events:
            items.append(
                CalendarEvent(
                    id=event.id,
                    public_id=event.public_id,
                    kind="TESTING",
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
                    testing_sessions=tuple(
                        CalendarTestingSession(
                            public_id=session.public_id,
                            session_order=session.session_order,
                            name=session.name,
                            start_datetime=session.start_datetime,
                            end_datetime=session.end_datetime,
                            scheduled_start_datetime=session.scheduled_start_datetime,
                            scheduled_end_datetime=session.scheduled_end_datetime,
                        )
                        for session in sorted(event.sessions, key=lambda s: s.session_order)
                    ),
                    race_sessions=(),
                )
            )

        for event in race_events:
            items.append(
                CalendarEvent(
                    id=event.id,
                    public_id=event.public_id,
                    kind="RACE",
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
                    testing_sessions=(),
                    race_sessions=tuple(
                        CalendarRaceSession(
                            public_id=session.public_id,
                            session_type=session.session_type.value,
                            start_datetime=session.start_datetime,
                            scheduled_start_datetime=session.scheduled_start_datetime,
                            lock_cutoff=session.lock_cutoff,
                            scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                            status=session.status.value,
                            status_reason=session.status_reason,
                        )
                        for session in sorted(
                            event.event_sessions,
                            key=lambda s: (s.scheduled_start_datetime or s.start_datetime, s.id),
                        )
                    ),
                )
            )

        return items

    def _testing_stmt(self, *, season_year: int | None):
        stmt = (
            select(TestingEvent)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit).joinedload(Circuit.country),
                selectinload(TestingEvent.sessions),
            )
        )

        if season_year is not None:
            stmt = stmt.join(TestingEvent.season).where(Season.year == season_year)
        else:
            stmt = stmt.join(TestingEvent.season).where(Season.is_active.is_(True))

        return stmt

    def _race_stmt(self, *, season_year: int | None):
        stmt = (
            select(RaceEvent)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit).joinedload(Circuit.country),
                selectinload(RaceEvent.event_sessions),
            )
        )

        if season_year is not None:
            stmt = stmt.join(RaceEvent.season).where(Season.year == season_year)
        else:
            stmt = stmt.join(RaceEvent.season).where(Season.is_active.is_(True))

        return stmt