from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Circuit, Season, TestingEvent, TestingEventSession
from app.domain.admin.testing_events.ports import AdminTestingEventRepository


class SqlAlchemyAdminTestingEventRepository(AdminTestingEventRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, testing_event_id: int) -> TestingEvent | None:
        return self._session.get(TestingEvent, testing_event_id)

    def get_season_by_year(self, year: int) -> Season | None:
        stmt = select(Season).where(Season.year == year)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_circuit_by_code(self, code: str) -> Circuit | None:
        stmt = select(Circuit).where(Circuit.code == code)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_season_and_name(self, *, season_id: int, name: str) -> TestingEvent | None:
        stmt = select(TestingEvent).where(
            TestingEvent.season_id == season_id,
            TestingEvent.name == name,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        name: str,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ) -> TestingEvent:
        testing_event = TestingEvent(
            season_id=season_id,
            circuit_id=circuit_id,
            name=name,
            event_start=event_start,
            event_end=event_end,
            scheduled_event_start=scheduled_event_start,
            scheduled_event_end=scheduled_event_end,
            status_reason=status_reason,
        )

        if status is not None:
            testing_event.status = status

        testing_event.sessions = [
            TestingEventSession(
                session_order=session["session_order"],
                name=session["name"],
                start_datetime=session.get("start_datetime"),
                end_datetime=session.get("end_datetime"),
                scheduled_start_datetime=session.get("scheduled_start_datetime"),
                scheduled_end_datetime=session.get("scheduled_end_datetime"),
            )
            for session in sessions
        ]

        self._session.add(testing_event)
        self._session.flush()
        self._session.refresh(testing_event)

        return testing_event

    def update(
        self,
        *,
        testing_event: TestingEvent,
        season_id: int,
        circuit_id: int,
        name: str,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ) -> TestingEvent:
        testing_event.season_id = season_id
        testing_event.circuit_id = circuit_id
        testing_event.name = name
        testing_event.event_start = event_start
        testing_event.event_end = event_end
        testing_event.scheduled_event_start = scheduled_event_start
        testing_event.scheduled_event_end = scheduled_event_end
        testing_event.status_reason = status_reason
        if status is not None:
            testing_event.status = status

        testing_event.sessions.clear()
        self._session.flush()
        testing_event.sessions.extend(
            [
                TestingEventSession(
                    session_order=session["session_order"],
                    name=session["name"],
                    start_datetime=session.get("start_datetime"),
                    end_datetime=session.get("end_datetime"),
                    scheduled_start_datetime=session.get("scheduled_start_datetime"),
                    scheduled_end_datetime=session.get("scheduled_end_datetime"),
                )
                for session in sessions
            ]
        )

        self._session.flush()
        self._session.refresh(testing_event)
        return testing_event
