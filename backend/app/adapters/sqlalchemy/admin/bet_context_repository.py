from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.betting import BetContext
from app.db.competition import RaceEvent, Season, TestingEvent
from app.db.enums import BetContextKind
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole
from app.domain.admin.bet_contexts.ports import (
    AdminBetContextRaceEvent,
    AdminBetContextRepository,
    AdminBetContextTestingEvent,
)


class SqlAlchemyAdminBetContextRepository(AdminBetContextRepository):
    def __init__(self, session: Session):
        self._session = session

    def season_exists(self, *, season_id: int) -> bool:
        stmt = select(Season.id).where(Season.id == season_id)
        return self._session.execute(stmt).scalar_one_or_none() is not None

    def group_exists(self, *, group_id: int) -> bool:
        stmt = select(Group.id).where(Group.id == group_id)
        return self._session.execute(stmt).scalar_one_or_none() is not None

    def list_group_ids(self, *, group_id: int | None) -> list[int]:
        if group_id is not None:
            return [group_id]

        stmt = select(Group.id).order_by(Group.id.asc())
        return list(self._session.execute(stmt).scalars().all())

    def list_race_events_for_season(self, *, season_id: int) -> list[AdminBetContextRaceEvent]:
        stmt = (
            select(RaceEvent)
            .where(RaceEvent.season_id == season_id)
            .order_by(RaceEvent.round_number.asc(), RaceEvent.id.asc())
        )
        race_events = self._session.execute(stmt).scalars().all()

        return [
            AdminBetContextRaceEvent(
                id=race_event.id,
                season_id=race_event.season_id,
                name=race_event.name,
            )
            for race_event in race_events
        ]

    def list_testing_events_for_season(self, *, season_id: int) -> list[AdminBetContextTestingEvent]:
        stmt = (
            select(TestingEvent)
            .where(TestingEvent.season_id == season_id)
            .order_by(TestingEvent.id.asc())
        )
        testing_events = self._session.execute(stmt).scalars().all()

        return [
            AdminBetContextTestingEvent(
                id=testing_event.id,
                season_id=testing_event.season_id,
                name=testing_event.name,
            )
            for testing_event in testing_events
        ]

    def ensure_season_context(
        self,
        *,
        group_id: int,
        season_id: int,
        label: str,
    ) -> bool:
        stmt = (
            select(BetContext)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.SEASON,
                BetContext.season_id == season_id,
                BetContext.race_event_id.is_(None),
                BetContext.testing_event_id.is_(None),
            )
        )
        existing = self._session.execute(stmt).scalar_one_or_none()
        if existing is not None:
            return False

        context = BetContext(
            kind=BetContextKind.SEASON,
            season_id=season_id,
            race_event_id=None,
            testing_event_id=None,
            label=label,
            results_published=False,
            results_published_at=None,
            group_id=group_id,
        )
        self._session.add(context)
        self._session.flush()
        return True

    def ensure_race_event_context(
        self,
        *,
        group_id: int,
        season_id: int,
        race_event_id: int,
        label: str,
    ) -> bool:
        stmt = (
            select(BetContext)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.GP,
                BetContext.race_event_id == race_event_id,
                BetContext.testing_event_id.is_(None),
            )
        )
        existing = self._session.execute(stmt).scalar_one_or_none()
        if existing is not None:
            return False

        context = BetContext(
            kind=BetContextKind.GP,
            season_id=season_id,
            race_event_id=race_event_id,
            testing_event_id=None,
            label=label,
            results_published=False,
            results_published_at=None,
            group_id=group_id,
        )
        self._session.add(context)
        self._session.flush()
        return True

    def ensure_testing_event_context(
        self,
        *,
        group_id: int,
        season_id: int,
        testing_event_id: int,
        label: str,
    ) -> bool:
        stmt = (
            select(BetContext)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.PRETESTING,
                BetContext.race_event_id.is_(None),
                BetContext.testing_event_id == testing_event_id,
            )
        )
        existing = self._session.execute(stmt).scalar_one_or_none()
        if existing is not None:
            return False

        context = BetContext(
            kind=BetContextKind.PRETESTING,
            season_id=season_id,
            race_event_id=None,
            testing_event_id=testing_event_id,
            label=label,
            results_published=False,
            results_published_at=None,
            group_id=group_id,
        )
        self._session.add(context)
        self._session.flush()
        return True
    
    def get_group_role(
        self,
        *,
        user_id: int,
        group_id: int,
    ) -> GroupRole | None:
        stmt = select(GroupMembership.role).where(
            GroupMembership.user_id == user_id,
            GroupMembership.group_id == group_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()