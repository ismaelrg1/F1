from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.betting import BetContext, BetTemplate, BetTemplateItem
from app.db.competition import DriverEntry, EventSession, RaceEvent, Season, SeasonDriver, TestingEvent
from app.db.enums import BetContextKind


class SqlAlchemyBetQuestionsRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_race_event_by_public_id(self, public_id: UUID) -> RaceEvent | None:
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
        return self._session.execute(stmt).scalar_one_or_none()
    
    def get_testing_event_by_public_id(self, public_id: UUID) -> TestingEvent | None:
        stmt = (
            select(TestingEvent)
            .where(TestingEvent.public_id == public_id)
            .options(
                joinedload(TestingEvent.season).selectinload(Season.driver_entries).joinedload(DriverEntry.driver),
                joinedload(TestingEvent.season).selectinload(Season.driver_entries).joinedload(DriverEntry.team),
                joinedload(TestingEvent.season).selectinload(Season.driver_entries).joinedload(DriverEntry.engine),
                joinedload(TestingEvent.season).selectinload(Season.season_drivers).joinedload(SeasonDriver.driver),
                selectinload(TestingEvent.sessions),
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()


    def get_gp_bet_context(self, *, group_id: int, race_event_id: int) -> BetContext | None:
        stmt = (
            select(BetContext)
            .where(
                BetContext.group_id == group_id,
                BetContext.race_event_id == race_event_id,
                BetContext.kind == BetContextKind.GP,
            )
            .options(selectinload(BetContext.bet_exceptions))
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def list_gp_templates_for_season(self, *, season_id: int) -> list[BetTemplate]:
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
        return list(self._session.execute(stmt).scalars().unique().all())
    
    def list_pretesting_templates_for_season(self, *, season_id: int) -> list[BetTemplate]:
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

        return list(self._session.execute(stmt).scalars().unique().all())
