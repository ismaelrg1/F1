from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.competition import Circuit, RaceEvent, Season, TestingEvent
from app.db.enums import RaceEventStatus, TestingEventStatus


class SqlAlchemyHomeRepository:
    def __init__(self, session: Session):
        self._session = session

    def _get_next_race_for_active_season(self) -> RaceEvent | None:
        now = datetime.now(UTC)
        start_at = func.coalesce(RaceEvent.event_start, RaceEvent.scheduled_event_start)

        stmt = (
            select(RaceEvent)
            .join(RaceEvent.season)
            .join(RaceEvent.circuit)
            .join(Circuit.country)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit).joinedload(Circuit.country),
            )
            .where(Season.is_active.is_(True))
            .where(start_at.is_not(None))
            .where(start_at >= now)
            .where(
                or_(
                    RaceEvent.status == RaceEventStatus.SCHEDULED,
                    RaceEvent.status == RaceEventStatus.POSTPONED,
                )
            )
            .order_by(start_at.asc(), RaceEvent.round_number.asc(), RaceEvent.id.asc())
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def _get_next_testing_for_active_season(self) -> TestingEvent | None:
        now = datetime.now(UTC)
        start_at = func.coalesce(TestingEvent.event_start, TestingEvent.scheduled_event_start)

        stmt = (
            select(TestingEvent)
            .join(TestingEvent.season)
            .join(TestingEvent.circuit)
            .join(Circuit.country)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit).joinedload(Circuit.country),
            )
            .where(Season.is_active.is_(True))
            .where(start_at.is_not(None))
            .where(start_at >= now)
            .where(
                or_(
                    TestingEvent.status == TestingEventStatus.SCHEDULED,
                    TestingEvent.status == TestingEventStatus.POSTPONED,
                )
            )
            .order_by(start_at.asc(), TestingEvent.id.asc())
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_next_event_for_active_season(self) -> RaceEvent | TestingEvent | None:
        next_race = self._get_next_race_for_active_season()
        next_testing = self._get_next_testing_for_active_season()

        if next_race is None:
            return next_testing
        if next_testing is None:
            return next_race

        race_start = next_race.event_start or next_race.scheduled_event_start
        testing_start = next_testing.event_start or next_testing.scheduled_event_start

        if race_start is None:
            return next_testing
        if testing_start is None:
            return next_race

        return next_race if race_start <= testing_start else next_testing
