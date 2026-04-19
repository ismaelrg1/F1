from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.competition import RaceEvent, TestingEvent, Circuit
from app.db.enums import RaceEventStatus, TestingEventStatus

from app.domain.home.models import HomeEvent, HomeEventResult

from app.domain.home.ports import HomeRepository


class SqlAlchemyHomeRepository(HomeRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_next_event_for_active_season(self) -> HomeEventResult | None:
        testing_events = list(self._session.execute(self._testing_stmt()).scalars().unique().all())
        race_events = list(self._session.execute(self._race_stmt()).scalars().unique().all())

        now = datetime.now(UTC)

        candidates: list[HomeEventResult] = []

        for event in testing_events:
            event_datetime = event.event_start or event.scheduled_event_start
            if event_datetime is None:
                continue
            if event_datetime < now:
                continue
            if event.status not in {TestingEventStatus.SCHEDULED, TestingEventStatus.POSTPONED}:
                continue

            candidates.append(self._map_testing_event(event))

        for event in race_events:
            event_datetime = event.event_start or event.scheduled_event_start
            if event_datetime is None:
                continue
            if event_datetime < now:
                continue
            if event.status not in {RaceEventStatus.SCHEDULED, RaceEventStatus.POSTPONED}:
                continue

            candidates.append(self._map_race_event(event))

        if not candidates:
            return None
        
        return min(
            candidates,
            key=lambda item: (
                item.event.event_start or item.event.scheduled_event_start or datetime.max.replace(tzinfo=UTC),
                item.event.round_number or 0,
            ),
        )

    def _testing_stmt(self):
        return (
            select(TestingEvent)
            .join(TestingEvent.season)
            .where(TestingEvent.season.has(is_active=True))
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit).joinedload(Circuit.country),
            )
        )

    def _race_stmt(self):
        return (
            select(RaceEvent)
            .join(RaceEvent.season)
            .where(RaceEvent.season.has(is_active=True))
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit).joinedload(Circuit.country),
            )
        )
    
    @staticmethod
    def _map_testing_event(event: TestingEvent) -> HomeEventResult:
        return HomeEventResult(
            kind="TESTING",
            event=HomeEvent(
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
            ),
        )

    @staticmethod
    def _map_race_event(event: RaceEvent) -> HomeEventResult:
        return HomeEventResult(
            kind="RACE",
            event=HomeEvent(
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
            ),
        )
