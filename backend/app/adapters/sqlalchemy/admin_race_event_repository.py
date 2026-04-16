from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, joinedload

from app.db.competition import Circuit, EventSession, RaceEvent, Season
from app.db.enums import RaceEventStatus, SessionType, SourceProvider
from app.domain.admin.race_events.models import (
    AdminRaceEvent,
    AdminRaceEventCircuit,
    AdminRaceEventSeason,
    AdminRaceEventSession,
    AdminRaceEventSessionWrite,
)
from app.domain.admin.race_events.ports import AdminRaceEventRepository


class SqlAlchemyAdminRaceEventRepository(AdminRaceEventRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, race_event_id: int) -> AdminRaceEvent | None:
        stmt = (
            select(RaceEvent)
            .where(RaceEvent.id == race_event_id)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit),
                selectinload(RaceEvent.event_sessions),
            )
        )
        race_event = self._session.execute(stmt).scalar_one_or_none()
        return None if race_event is None else self._map_race_event(race_event)

    def get_season_by_year(self, year: int) -> AdminRaceEventSeason | None:
        stmt = select(Season).where(Season.year == year)
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None
        return AdminRaceEventSeason(id=season.id, year=season.year)

    def get_circuit_by_code(self, code: str) -> AdminRaceEventCircuit | None:
        stmt = select(Circuit).where(Circuit.code == code)
        circuit = self._session.execute(stmt).scalar_one_or_none()
        if circuit is None:
            return None
        return AdminRaceEventCircuit(id=circuit.id, code=circuit.code)

    def get_by_season_and_round(self, *, season_id: int, round_number: int) -> AdminRaceEvent | None:
        stmt = (
            select(RaceEvent)
            .where(
                RaceEvent.season_id == season_id,
                RaceEvent.round_number == round_number,
            )
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit),
                selectinload(RaceEvent.event_sessions),
            )
        )
        race_event = self._session.execute(stmt).scalar_one_or_none()
        return None if race_event is None else self._map_race_event(race_event)

    def list_race_events(self, *, season_year: int | None = None) -> list[AdminRaceEvent]:
        stmt = (
            select(RaceEvent)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit),
                selectinload(RaceEvent.event_sessions),
            )
            .order_by(RaceEvent.round_number.asc(), RaceEvent.id.asc())
        )

        if season_year is not None:
            stmt = stmt.join(RaceEvent.season).where(Season.year == season_year)

        items = self._session.execute(stmt).scalars().unique().all()
        return [self._map_race_event(item) for item in items]

    def create(
        self,
        *,
        season_id: int,
        circuit_id: int,
        round_number: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminRaceEventSessionWrite],
    ) -> AdminRaceEvent:
        race_event = RaceEvent(
            season_id=season_id,
            circuit_id=circuit_id,
            round_number=round_number,
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
            race_event.status = RaceEventStatus(status)

        race_event.event_sessions = [
            self._build_event_session(session)
            for session in sessions
        ]

        self._session.add(race_event)
        self._session.flush()

        stmt = (
            select(RaceEvent)
            .where(RaceEvent.id == race_event.id)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit),
                selectinload(RaceEvent.event_sessions),
            )
        )
        created = self._session.execute(stmt).scalar_one()
        return self._map_race_event(created)

    def update(
        self,
        *,
        race_event_id: int,
        season_id: int,
        circuit_id: int,
        round_number: int,
        name: str,
        source_provider: str,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status: str | None,
        status_reason: str | None,
        sessions: list[AdminRaceEventSessionWrite],
    ) -> AdminRaceEvent:
        race_event = self._session.get(RaceEvent, race_event_id)
        if race_event is None:
            raise ValueError(f"Race event {race_event_id} not found")

        race_event.season_id = season_id
        race_event.circuit_id = circuit_id
        race_event.round_number = round_number
        race_event.name = name
        race_event.source_provider = SourceProvider(source_provider)
        race_event.source_key = source_key
        race_event.event_start = event_start
        race_event.event_end = event_end
        race_event.scheduled_event_start = scheduled_event_start
        race_event.scheduled_event_end = scheduled_event_end
        race_event.status_reason = status_reason
        if status is not None:
            race_event.status = RaceEventStatus(status)

        race_event.event_sessions.clear()
        self._session.flush()

        for session in sessions:
            race_event.event_sessions.append(self._build_event_session(session))

        self._session.flush()

        stmt = (
            select(RaceEvent)
            .where(RaceEvent.id == race_event.id)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit),
                selectinload(RaceEvent.event_sessions),
            )
        )
        updated = self._session.execute(stmt).scalar_one()
        return self._map_race_event(updated)

    def _build_event_session(self, session: AdminRaceEventSessionWrite) -> EventSession:
        event_session = EventSession(
            session_type=SessionType(session.session_type),
            source_provider=SourceProvider(session.source_provider),
            source_key=session.source_key,
            start_datetime=session.start_datetime,
            scheduled_start_datetime=session.scheduled_start_datetime,
            lock_cutoff=session.lock_cutoff,
            scheduled_lock_cutoff=session.scheduled_lock_cutoff,
            status_reason=session.status_reason,
        )
        if session.status is not None:
            event_session.status = RaceEventStatus(session.status)
        return event_session

    def _map_race_event(self, race_event: RaceEvent) -> AdminRaceEvent:
        return AdminRaceEvent(
            id=race_event.id,
            public_id=race_event.public_id,
            season_year=race_event.season.year,
            round_number=race_event.round_number,
            circuit_code=race_event.circuit.code,
            name=race_event.name,
            source_provider=race_event.source_provider.value,
            source_key=race_event.source_key,
            event_start=race_event.event_start,
            event_end=race_event.event_end,
            scheduled_event_start=race_event.scheduled_event_start,
            scheduled_event_end=race_event.scheduled_event_end,
            status=race_event.status.value,
            status_reason=race_event.status_reason,
            sessions=[
                AdminRaceEventSession(
                    id=session.id,
                    public_id=session.public_id,
                    session_type=session.session_type.value,
                    source_provider=session.source_provider.value,
                    source_key=session.source_key,
                    start_datetime=session.start_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    lock_cutoff=session.lock_cutoff,
                    scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                    status=session.status.value,
                    status_reason=session.status_reason,
                    results_published=session.results_published,
                    results_published_at=session.results_published_at,
                )
                for session in sorted(
                    race_event.event_sessions,
                    key=lambda s: s.start_datetime,
                )
            ],
        )