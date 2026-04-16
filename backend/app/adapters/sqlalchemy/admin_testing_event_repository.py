from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.competition import Circuit, Season, TestingEvent, TestingEventSession
from app.db.enums import SourceProvider, TestingEventStatus
from app.domain.admin.testing_events.models import (
    AdminTestingEvent,
    AdminTestingEventCircuit,
    AdminTestingEventSeason,
    AdminTestingEventSession,
    AdminTestingEventSessionWrite,
)
from app.domain.admin.testing_events.ports import AdminTestingEventRepository


class SqlAlchemyAdminTestingEventRepository(AdminTestingEventRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, testing_event_id: int) -> AdminTestingEvent | None:
        stmt = (
            select(TestingEvent)
            .where(TestingEvent.id == testing_event_id)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit),
                selectinload(TestingEvent.sessions),
            )
        )
        testing_event = self._session.execute(stmt).scalar_one_or_none()
        return None if testing_event is None else self._map_testing_event(testing_event)

    def get_season_by_year(self, year: int) -> AdminTestingEventSeason | None:
        stmt = select(Season).where(Season.year == year)
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None
        return AdminTestingEventSeason(id=season.id, year=season.year)

    def get_circuit_by_code(self, code: str) -> AdminTestingEventCircuit | None:
        stmt = select(Circuit).where(Circuit.code == code)
        circuit = self._session.execute(stmt).scalar_one_or_none()
        if circuit is None:
            return None
        return AdminTestingEventCircuit(id=circuit.id, code=circuit.code)

    def get_by_season_and_name(self, *, season_id: int, name: str) -> AdminTestingEvent | None:
        stmt = (
            select(TestingEvent)
            .where(
                TestingEvent.season_id == season_id,
                TestingEvent.name == name,
            )
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit),
                selectinload(TestingEvent.sessions),
            )
        )
        testing_event = self._session.execute(stmt).scalar_one_or_none()
        return None if testing_event is None else self._map_testing_event(testing_event)

    def list_testing_events(self, *, season_year: int | None = None) -> list[AdminTestingEvent]:
        stmt = (
            select(TestingEvent)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit),
                selectinload(TestingEvent.sessions),
            )
            .order_by(TestingEvent.id.asc())
        )

        if season_year is not None:
            stmt = stmt.join(TestingEvent.season).where(Season.year == season_year)

        items = self._session.execute(stmt).scalars().unique().all()
        return [self._map_testing_event(item) for item in items]

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminTestingEventSessionWrite],
    ) -> AdminTestingEvent:
        testing_event = TestingEvent(
            season_id=season_id,
            circuit_id=circuit_id,
            name=name,
            source_provider=SourceProvider(source_provider),
            source_key=source_key,
            event_start=event_start,
            event_end=event_end,
            scheduled_event_start=scheduled_event_start,
            scheduled_event_end=scheduled_event_end,
            status_reason=status_reason,
        )

        if status is not None:
            testing_event.status = TestingEventStatus(status)

        testing_event.sessions = [
            TestingEventSession(
                session_order=session.session_order,
                name=session.name,
                source_provider=SourceProvider(session.source_provider),
                source_key=session.source_key,
                start_datetime=session.start_datetime,
                end_datetime=session.end_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                scheduled_end_datetime=session.scheduled_end_datetime,
            )
            for session in sessions
        ]

        self._session.add(testing_event)
        self._session.flush()

        stmt = (
            select(TestingEvent)
            .where(TestingEvent.id == testing_event.id)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit),
                selectinload(TestingEvent.sessions),
            )
        )
        created = self._session.execute(stmt).scalar_one()
        return self._map_testing_event(created)

    def update(
        self,
        *,
        testing_event_id: int,
        season_id: int,
        circuit_id: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminTestingEventSessionWrite],
    ) -> AdminTestingEvent:
        testing_event = self._session.get(TestingEvent, testing_event_id)
        if testing_event is None:
            raise ValueError(f"Testing event {testing_event_id} not found")

        testing_event.season_id = season_id
        testing_event.circuit_id = circuit_id
        testing_event.name = name
        testing_event.source_provider = SourceProvider(source_provider)
        testing_event.source_key = source_key
        testing_event.event_start = event_start
        testing_event.event_end = event_end
        testing_event.scheduled_event_start = scheduled_event_start
        testing_event.scheduled_event_end = scheduled_event_end
        testing_event.status_reason = status_reason
        if status is not None:
            testing_event.status = TestingEventStatus(status)

        testing_event.sessions.clear()
        self._session.flush()

        testing_event.sessions.extend(
            [
                TestingEventSession(
                    session_order=session.session_order,
                    name=session.name,
                    source_provider=SourceProvider(session.source_provider),
                    source_key=session.source_key,
                    start_datetime=session.start_datetime,
                    end_datetime=session.end_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    scheduled_end_datetime=session.scheduled_end_datetime,
                )
                for session in sessions
            ]
        )

        self._session.flush()

        stmt = (
            select(TestingEvent)
            .where(TestingEvent.id == testing_event.id)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit),
                selectinload(TestingEvent.sessions),
            )
        )
        updated = self._session.execute(stmt).scalar_one()
        return self._map_testing_event(updated)

    def _map_testing_event(self, testing_event: TestingEvent) -> AdminTestingEvent:
        return AdminTestingEvent(
            id=testing_event.id,
            public_id=testing_event.public_id,
            season_year=testing_event.season.year,
            circuit_code=testing_event.circuit.code,
            name=testing_event.name,
            source_provider=testing_event.source_provider.value,
            source_key=testing_event.source_key,
            event_start=testing_event.event_start,
            event_end=testing_event.event_end,
            scheduled_event_start=testing_event.scheduled_event_start,
            scheduled_event_end=testing_event.scheduled_event_end,
            status=testing_event.status.value,
            status_reason=testing_event.status_reason,
            sessions=[
                AdminTestingEventSession(
                    id=session.id,
                    public_id=session.public_id,
                    session_order=session.session_order,
                    name=session.name,
                    source_provider=session.source_provider.value,
                    source_key=session.source_key,
                    start_datetime=session.start_datetime,
                    end_datetime=session.end_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    scheduled_end_datetime=session.scheduled_end_datetime,
                )
                for session in sorted(testing_event.sessions, key=lambda s: s.session_order)
            ],
        )