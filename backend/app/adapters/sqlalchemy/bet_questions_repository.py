from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.betting import BetContext, BetTemplate, BetTemplateItem
from app.db.competition import (
    DriverEntry,
    EventSession,
    RaceEvent,
    Season,
    SeasonDriver,
    TestingEvent,
)
from app.db.enums import BetContextKind
from app.domain.bets.enums import BetTemplateScope, BetValueType
from app.domain.bets.models import (
    BetContextDefinition,
    BetExceptionDefinition,
    BetRaceEvent,
    BetRaceEventSession,
    BetRosterEntry,
    BetScoreDefinition,
    BetSeason,
    BetTemplateDefinition,
    BetTemplateItemDefinition,
    BetTestingEvent,
    BetTestingEventSession,
)
from app.domain.bets.ports import BetQuestionsRepository


class SqlAlchemyBetQuestionsRepository(BetQuestionsRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_race_event_by_public_id(self, public_id: UUID) -> BetRaceEvent | None:
        stmt = (
            select(RaceEvent)
            .where(RaceEvent.public_id == public_id)
            .options(
                joinedload(RaceEvent.season).selectinload(Season.driver_entries)
                .joinedload(DriverEntry.driver),
                joinedload(RaceEvent.season).selectinload(Season.driver_entries)
                .joinedload(DriverEntry.team),
                joinedload(RaceEvent.season).selectinload(Season.driver_entries)
                .joinedload(DriverEntry.engine),
                joinedload(RaceEvent.season).selectinload(Season.season_drivers)
                .joinedload(SeasonDriver.driver),
                selectinload(RaceEvent.driver_entries).joinedload(DriverEntry.driver),
                selectinload(RaceEvent.driver_entries).joinedload(DriverEntry.team),
                selectinload(RaceEvent.driver_entries).joinedload(DriverEntry.engine),
                selectinload(RaceEvent.event_sessions).selectinload(EventSession.driver_entries)
                .joinedload(DriverEntry.driver),
                selectinload(RaceEvent.event_sessions).selectinload(EventSession.driver_entries)
                .joinedload(DriverEntry.team),
                selectinload(RaceEvent.event_sessions).selectinload(EventSession.driver_entries)
                .joinedload(DriverEntry.engine),
            )
        )
        event = self._session.execute(stmt).scalar_one_or_none()
        if event is None:
            return None

        driver_numbers = {
            season_driver.driver_id: season_driver.driver_number
            for season_driver in event.season.season_drivers
        }

        return BetRaceEvent(
            id=event.id,
            public_id=event.public_id,
            season_id=event.season_id,
            event_start=event.event_start,
            scheduled_event_start=event.scheduled_event_start,
            season_driver_entries=tuple(
                self._map_driver_entry(entry, driver_numbers)
                for entry in event.season.driver_entries
                if entry.race_event_id is None and entry.event_session_id is None
            ),
            event_driver_entries=tuple(
                self._map_driver_entry(entry, driver_numbers)
                for entry in event.driver_entries
            ),
            sessions=tuple(
                BetRaceEventSession(
                    id=session.id,
                    public_id=session.public_id,
                    session_type=session.session_type.value,
                    start_datetime=session.start_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    lock_cutoff=session.lock_cutoff,
                    scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                    status=session.status.value,
                    driver_entries=tuple(
                        self._map_driver_entry(entry, driver_numbers)
                        for entry in session.driver_entries
                    ),
                )
                for session in event.event_sessions
            ),
        )

    def get_testing_event_by_public_id(self, public_id: UUID) -> BetTestingEvent | None:
        stmt = (
            select(TestingEvent)
            .where(TestingEvent.public_id == public_id)
            .options(
                joinedload(TestingEvent.season).selectinload(Season.driver_entries)
                .joinedload(DriverEntry.driver),
                joinedload(TestingEvent.season).selectinload(Season.driver_entries)
                .joinedload(DriverEntry.team),
                joinedload(TestingEvent.season).selectinload(Season.driver_entries)
                .joinedload(DriverEntry.engine),
                joinedload(TestingEvent.season).selectinload(Season.season_drivers)
                .joinedload(SeasonDriver.driver),
                selectinload(TestingEvent.sessions),
            )
        )
        event = self._session.execute(stmt).scalar_one_or_none()
        if event is None:
            return None

        driver_numbers = {
            season_driver.driver_id: season_driver.driver_number
            for season_driver in event.season.season_drivers
        }

        return BetTestingEvent(
            id=event.id,
            public_id=event.public_id,
            season_id=event.season_id,
            status=event.status.value,
            event_start=event.event_start,
            scheduled_event_start=event.scheduled_event_start,
            season_driver_entries=tuple(
                self._map_driver_entry(entry, driver_numbers)
                for entry in event.season.driver_entries
                if entry.race_event_id is None and entry.event_session_id is None
            ),
            sessions=tuple(
                BetTestingEventSession(
                    id=session.id,
                    public_id=session.public_id,
                    session_order=session.session_order,
                    name=session.name,
                    start_datetime=session.start_datetime,
                    end_datetime=session.end_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    scheduled_end_datetime=session.scheduled_end_datetime,
                )
                for session in event.sessions
            ),
        )
    
    def get_season_by_year(self, year: int) -> BetSeason | None:
        stmt = (
            select(Season)
            .where(Season.year == year)
            .options(
                selectinload(Season.driver_entries).joinedload(DriverEntry.driver),
                selectinload(Season.driver_entries).joinedload(DriverEntry.team),
                selectinload(Season.driver_entries).joinedload(DriverEntry.engine),
                selectinload(Season.season_drivers).joinedload(SeasonDriver.driver),
            )
        )
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None

        driver_numbers = {
            season_driver.driver_id: season_driver.driver_number
            for season_driver in season.season_drivers
        }

        return BetSeason(
            id=season.id,
            year=season.year,
            season_driver_entries=tuple(
                self._map_driver_entry(entry, driver_numbers)
                for entry in season.driver_entries
                if entry.race_event_id is None and entry.event_session_id is None
            ),
        )

    def get_season_bet_context(self, *, group_id: int, season_id: int) -> BetContextDefinition | None:
        stmt = (
            select(BetContext)
            .where(
                BetContext.group_id == group_id,
                BetContext.season_id == season_id,
                BetContext.kind == BetContextKind.SEASON,
            )
            .options(selectinload(BetContext.bet_exceptions))
        )
        context = self._session.execute(stmt).scalar_one_or_none()
        return self._map_bet_context(context)

    def list_season_templates_for_season(self, *, season_id: int) -> list[BetTemplateDefinition]:
        stmt = (
            select(BetTemplate)
            .where(
                BetTemplate.season_id == season_id,
                BetTemplate.context_kind == BetContextKind.SEASON,
            )
            .options(
                selectinload(BetTemplate.items).joinedload(BetTemplateItem.bet_score),
            )
        )
        templates = self._session.execute(stmt).scalars().unique().all()
        return [self._map_template(template) for template in templates]

    def get_gp_bet_context(self, *, group_id: int, race_event_id: int) -> BetContextDefinition | None:
        stmt = (
            select(BetContext)
            .where(
                BetContext.group_id == group_id,
                BetContext.race_event_id == race_event_id,
                BetContext.kind == BetContextKind.GP,
            )
            .options(selectinload(BetContext.bet_exceptions))
        )
        context = self._session.execute(stmt).scalar_one_or_none()
        return self._map_bet_context(context)

    def get_pretesting_bet_context(self, *, group_id: int, testing_event_id: int) -> BetContextDefinition | None:
        stmt = (
            select(BetContext)
            .where(
                BetContext.group_id == group_id,
                BetContext.testing_event_id == testing_event_id,
                BetContext.kind == BetContextKind.PRETESTING,
            )
            .options(selectinload(BetContext.bet_exceptions))
        )
        context = self._session.execute(stmt).scalar_one_or_none()
        return self._map_bet_context(context)

    def list_gp_templates_for_season(self, *, season_id: int) -> list[BetTemplateDefinition]:
        stmt = (
            select(BetTemplate)
            .where(
                BetTemplate.season_id == season_id,
                BetTemplate.context_kind == BetContextKind.GP,
            )
            .options(
                selectinload(BetTemplate.items).joinedload(BetTemplateItem.bet_score),
            )
        )
        templates = self._session.execute(stmt).scalars().unique().all()
        return [self._map_template(template) for template in templates]

    def list_pretesting_templates_for_season(self, *, season_id: int) -> list[BetTemplateDefinition]:
        stmt = (
            select(BetTemplate)
            .where(
                BetTemplate.season_id == season_id,
                BetTemplate.context_kind == BetContextKind.PRETESTING,
            )
            .options(
                selectinload(BetTemplate.items).joinedload(BetTemplateItem.bet_score),
            )
        )
        templates = self._session.execute(stmt).scalars().unique().all()
        return [self._map_template(template) for template in templates]

    @staticmethod
    def _map_driver_entry(entry: DriverEntry, driver_numbers: dict[int, int | None]) -> BetRosterEntry:
        return BetRosterEntry(
            driver_id=entry.driver_id,
            driver_code=entry.driver.code,
            driver_name=entry.driver.name,
            driver_number=driver_numbers.get(entry.driver_id),
            team_id=entry.team_id,
            team_code=entry.team.code,
            team_name=entry.team.name,
            engine_id=entry.engine_id,
            engine_code=entry.engine.code,
            engine_name=entry.engine.name,
            seat_index=entry.seat_index,
            active_from=entry.active_from,
            active_to=entry.active_to,
        )

    @staticmethod
    def _map_bet_context(context: BetContext | None) -> BetContextDefinition | None:
        if context is None:
            return None

        return BetContextDefinition(
            public_id=context.public_id,
            kind=context.kind.value,
            label=context.label,
            exceptions=tuple(
                BetExceptionDefinition(
                    event_session_id=exception.event_session_id,
                    bet_score_id=exception.bet_score_id,
                    override_points=exception.override_points,
                    is_disabled=exception.is_disabled,
                    override_constraints_json=exception.override_constraints_json,
                )
                for exception in context.bet_exceptions
            ),
        )

    @staticmethod
    def _map_template(template: BetTemplate) -> BetTemplateDefinition:
        return BetTemplateDefinition(
            scope=BetTemplateScope(template.scope.value),
            session_type=template.session_type.value if template.session_type is not None else None,
            items=tuple(
                BetTemplateItemDefinition(
                    id=item.id,
                    required=item.required,
                    display_order=item.display_order,
                    bet_score=BetScoreDefinition(
                        id=item.bet_score.id,
                        code=item.bet_score.code,
                        label=item.bet_score.label,
                        base_points=item.bet_score.base_points,
                        value_type=BetValueType(item.bet_score.value_type.value),
                        constraints_json=item.bet_score.constraints_json,
                    ),
                )
                for item in template.items
            ),
        )
