from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Circuit, EventSession, RaceEvent, Season
from app.domain.admin.race_events.ports import AdminRaceEventRepository


class SqlAlchemyAdminRaceEventRepository(AdminRaceEventRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_season_by_year(self, year: int) -> Season | None:
        stmt = select(Season).where(Season.year == year)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_circuit_by_code(self, code: str) -> Circuit | None:
        stmt = select(Circuit).where(Circuit.code == code)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_season_and_round(self, *, season_id: int, round_number: int) -> RaceEvent | None:
        stmt = select(RaceEvent).where(
            RaceEvent.season_id == season_id,
            RaceEvent.round_number == round_number,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        round_number: int,
        name: str,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ) -> RaceEvent:
        race_event = RaceEvent(
            season_id=season_id,
            circuit_id=circuit_id,
            round_number=round_number,
            name=name,
            event_start=event_start,
            event_end=event_end,
            scheduled_event_start=scheduled_event_start,
            scheduled_event_end=scheduled_event_end,
            status_reason=status_reason,
        )

        if status is not None:
            race_event.status = status

        event_sessions: list[EventSession] = []
        for session in sessions:
            event_session = EventSession(
                session_type=session["session_type"],
                start_datetime=session["start_datetime"],
                scheduled_start_datetime=session.get("scheduled_start_datetime"),
                lock_cutoff=session["lock_cutoff"],
                scheduled_lock_cutoff=session.get("scheduled_lock_cutoff"),
                status_reason=session.get("status_reason"),
            )
            if session.get("status") is not None:
                event_session.status = session["status"]
            event_sessions.append(event_session)

        race_event.event_sessions = event_sessions

        self._session.add(race_event)
        self._session.flush()
        self._session.refresh(race_event)

        return race_event