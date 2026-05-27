from sqlalchemy import exists, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.betting import BetContext
from app.db.competition import Circuit, RaceEvent, Season, TestingEvent
from app.db.enums import BetContextKind
from app.db.scoring import OfficialResult, ResultPublication
from app.domain.management.calendar import (
    ManagementCalendarCountry,
    ManagementCalendarEvent,
    ManagementCalendarRepository,
    ManagementCalendarSession,
)


class SqlAlchemyManagementCalendarRepository(ManagementCalendarRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_events(
        self,
        *,
        season_year: int | None,
        group_id: int,
    ) -> list[ManagementCalendarEvent]:
        race_events = self._session.execute(
            self._race_events_stmt(season_year=season_year)
        ).scalars().unique().all()

        testing_events = self._session.execute(
            self._testing_events_stmt(season_year=season_year)
        ).scalars().unique().all()

        items: list[ManagementCalendarEvent] = []

        for event in testing_events:
            context = self._get_testing_context(group_id=group_id, testing_event_id=event.id)
            items.append(self._map_testing_event(event, context))

        for event in race_events:
            context = self._get_race_context(group_id=group_id, race_event_id=event.id)
            items.append(self._map_race_event(event, context))

        return sorted(
            items,
            key=lambda item: (
                item.season_year,
                item.round_number if item.round_number is not None else -1,
                item.name,
            ),
        )

    def _race_events_stmt(self, *, season_year: int | None):
        stmt = (
            select(RaceEvent)
            .options(
                joinedload(RaceEvent.season),
                joinedload(RaceEvent.circuit).joinedload(Circuit.country),
                selectinload(RaceEvent.event_sessions),
            )
            .join(RaceEvent.season)
        )

        if season_year is None:
            return stmt.where(Season.is_active.is_(True))

        return stmt.where(Season.year == season_year)

    def _testing_events_stmt(self, *, season_year: int | None):
        stmt = (
            select(TestingEvent)
            .options(
                joinedload(TestingEvent.season),
                joinedload(TestingEvent.circuit).joinedload(Circuit.country),
                selectinload(TestingEvent.sessions),
            )
            .join(TestingEvent.season)
        )

        if season_year is None:
            return stmt.where(Season.is_active.is_(True))

        return stmt.where(Season.year == season_year)

    def _get_race_context(self, *, group_id: int, race_event_id: int) -> BetContext | None:
        return self._session.execute(
            select(BetContext).where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.GP,
                BetContext.race_event_id == race_event_id,
            )
        ).scalar_one_or_none()

    def _get_testing_context(self, *, group_id: int, testing_event_id: int) -> BetContext | None:
        return self._session.execute(
            select(BetContext).where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.PRETESTING,
                BetContext.testing_event_id == testing_event_id,
            )
        ).scalar_one_or_none()

    def _has_official_results(
        self,
        *,
        bet_context_id: int | None,
        event_session_id: int | None = None,
        testing_event_session_id: int | None = None,
    ) -> bool:
        if bet_context_id is None:
            return False

        stmt = select(
            exists().where(
                OfficialResult.bet_context_id == bet_context_id,
                OfficialResult.event_session_id.is_(event_session_id)
                if event_session_id is None
                else OfficialResult.event_session_id == event_session_id,
                OfficialResult.testing_event_session_id.is_(testing_event_session_id)
                if testing_event_session_id is None
                else OfficialResult.testing_event_session_id == testing_event_session_id,
            )
        )
        return bool(self._session.execute(stmt).scalar())

    def _results_published(
        self,
        *,
        bet_context_id: int | None,
        event_session_id: int | None = None,
        testing_event_session_id: int | None = None,
    ) -> bool:
        if bet_context_id is None:
            return False

        stmt = select(
            exists().where(
                ResultPublication.bet_context_id == bet_context_id,
                ResultPublication.event_session_id.is_(event_session_id)
                if event_session_id is None
                else ResultPublication.event_session_id == event_session_id,
                ResultPublication.testing_event_session_id.is_(testing_event_session_id)
                if testing_event_session_id is None
                else ResultPublication.testing_event_session_id == testing_event_session_id,
            )
        )
        return bool(self._session.execute(stmt).scalar())

    def _map_race_event(self, event: RaceEvent, context: BetContext | None):
        context_id = context.id if context is not None else None

        return ManagementCalendarEvent(
            type="RACE",
            public_id=event.public_id,
            season_year=event.season.year,
            round_number=event.round_number,
            name=event.name,
            country=ManagementCalendarCountry(
                name=event.circuit.country.name,
                flag_asset_url=event.circuit.country.flag_asset_url,
            ),
            sessions=tuple(
                ManagementCalendarSession(
                    public_id=session.public_id,
                    name=session.session_type.value,
                    type=session.session_type.value,
                    has_official_results=self._has_official_results(
                        bet_context_id=context_id,
                        event_session_id=session.id,
                    ),
                    results_published=self._results_published(
                        bet_context_id=context_id,
                        event_session_id=session.id,
                    ),
                )
                for session in sorted(
                    event.event_sessions,
                    key=lambda item: (item.scheduled_start_datetime or item.start_datetime, item.id),
                )
            ),
            has_bet_context=context is not None,
            has_official_results=self._has_official_results(bet_context_id=context_id),
            results_published=self._results_published(bet_context_id=context_id),
        )

    def _map_testing_event(self, event: TestingEvent, context: BetContext | None):
        context_id = context.id if context is not None else None

        return ManagementCalendarEvent(
            type="TESTING",
            public_id=event.public_id,
            season_year=event.season.year,
            round_number=None,
            name=event.name,
            country=ManagementCalendarCountry(
                name=event.circuit.country.name,
                flag_asset_url=event.circuit.country.flag_asset_url,
            ),
            sessions=tuple(
                ManagementCalendarSession(
                    public_id=session.public_id,
                    name=session.name,
                    type="TESTING",
                    has_official_results=self._has_official_results(
                        bet_context_id=context_id,
                        testing_event_session_id=session.id,
                    ),
                    results_published=self._results_published(
                        bet_context_id=context_id,
                        testing_event_session_id=session.id,
                    ),
                )
                for session in sorted(event.sessions, key=lambda item: item.session_order)
            ),
            has_bet_context=context is not None,
            has_official_results=self._has_official_results(bet_context_id=context_id),
            results_published=self._results_published(bet_context_id=context_id),
        )