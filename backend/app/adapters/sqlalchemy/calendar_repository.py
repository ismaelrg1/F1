from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.competition import Circuit, RaceEvent, Season, TestingEvent


class SqlAlchemyCalendarRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_testing_events(self, *, season_year: int | None = None) -> list[TestingEvent]:
        stmt = (
            select(TestingEvent)
            .join(TestingEvent.season)
            .join(TestingEvent.circuit)
            .join(Circuit.country)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit).joinedload(Circuit.country),
                selectinload(TestingEvent.sessions),
            )
            .order_by(
                TestingEvent.scheduled_event_start.asc().nullslast(),
                TestingEvent.id.asc(),
            )
        )

        if season_year is None:
            stmt = stmt.where(Season.is_active.is_(True))
        else:
            stmt = stmt.where(Season.year == season_year)

        return list(self._session.execute(stmt).scalars().unique().all())

    def list_race_events(self, *, season_year: int | None = None) -> list[RaceEvent]:
        stmt = (
            select(RaceEvent)
            .join(RaceEvent.season)
            .join(RaceEvent.circuit)
            .join(Circuit.country)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit).joinedload(Circuit.country),
                selectinload(RaceEvent.event_sessions),
            )
            .order_by(
                RaceEvent.scheduled_event_start.asc().nullslast(),
                RaceEvent.round_number.asc(),
                RaceEvent.id.asc(),
            )
        )

        if season_year is None:
            stmt = stmt.where(Season.is_active.is_(True))
        else:
            stmt = stmt.where(Season.year == season_year)

        return list(self._session.execute(stmt).scalars().unique().all())