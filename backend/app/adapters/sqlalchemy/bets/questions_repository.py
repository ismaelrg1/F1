from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.betting import BetContext, BetTemplate, BetTemplateItem, Bet, BetPick, BetScore, BetEditPermission, BetSubmissionRevision
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
    BetAnswerResult,
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
    UserBetDefinition,
    BetAnswerInput,
    BetEditPermissionDefinition,
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
            betting_open_at=event.betting_open_at,
            lock_cutoff=event.lock_cutoff,
            scheduled_lock_cutoff=event.scheduled_lock_cutoff,
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
                    betting_open_at=session.betting_open_at,
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
            betting_open_at=event.betting_open_at,
            lock_cutoff=event.lock_cutoff,
            scheduled_lock_cutoff=event.scheduled_lock_cutoff,
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
                    betting_open_at=session.betting_open_at,
                    lock_cutoff=session.lock_cutoff,
                    scheduled_lock_cutoff=session.scheduled_lock_cutoff,
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
            betting_open_at=season.betting_open_at,
            lock_cutoff=season.lock_cutoff,
            scheduled_lock_cutoff=season.scheduled_lock_cutoff,
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
    
    def list_user_bets_for_context(
        self,
        *,
        user_id: int,
        bet_context_id: int,
    ) -> list[UserBetDefinition]:
        stmt = (
            select(Bet)
            .where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
            )
            .options(
                selectinload(Bet.bet_picks).joinedload(BetPick.bet_score),
                selectinload(Bet.submission_revisions),
            )
        )
        bets = self._session.execute(stmt).scalars().unique().all()

        return [
            UserBetDefinition(
                event_session_id=bet.event_session_id,
                testing_event_session_id=getattr(bet, "testing_event_session_id", None),
                submitted_at=bet.submitted_at,
                last_modified_at=bet.last_modified_at,
                locked_at=bet.locked_at,
                picks=tuple(
                    BetAnswerResult(
                        bet_score_code=pick.bet_score.code,
                        value=pick.value,
                    )
                    for pick in sorted(bet.bet_picks, key=lambda p: (p.bet_score.code, p.id))
                ),
                revision_count=len(bet.submission_revisions),
            )
            for bet in bets
        ]
    
    def get_bet_score_ids_by_codes(self, *, codes: set[str]) -> dict[str, int]:
        if not codes:
            return {}

        stmt = select(BetScore).where(BetScore.code.in_(codes))
        scores = self._session.execute(stmt).scalars().all()

        return {
            score.code: score.id
            for score in scores
        }
    
    def upsert_user_bet_draft(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        answers: list[BetAnswerInput],
        modified_at: datetime,
    ) -> None:
        stmt = (
            select(Bet)
            .where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
                Bet.event_session_id.is_(None)
                if event_session_id is None
                else Bet.event_session_id == event_session_id,
                Bet.testing_event_session_id.is_(None)
                if testing_event_session_id is None
                else Bet.testing_event_session_id == testing_event_session_id,
            )
            .options(selectinload(Bet.bet_picks))
        )
        bet = self._session.execute(stmt).scalar_one_or_none()

        if bet is None:
            bet = Bet(
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
                submitted_at=None,
                last_modified_at=modified_at,
                locked_at=None,
            )
            self._session.add(bet)
            self._session.flush()
        else:
            bet.submitted_at = None
            bet.last_modified_at = modified_at
            bet.locked_at = None

        score_ids_by_code = self.get_bet_score_ids_by_codes(
            codes={answer.bet_score_code for answer in answers},
        )

        existing_picks_by_score_id = {
            pick.bet_score_id: pick
            for pick in bet.bet_picks
        }

        for answer in answers:
            bet_score_id = score_ids_by_code[answer.bet_score_code]
            existing_pick = existing_picks_by_score_id.get(bet_score_id)

            if existing_pick is None:
                self._session.add(
                    BetPick(
                        bet_id=bet.id,
                        bet_score_id=bet_score_id,
                        value=answer.value,
                    )
                )
            else:
                existing_pick.value = answer.value

        self._session.flush()

    def list_active_edit_permissions_for_scope(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        now: datetime,
    ) -> list[BetEditPermissionDefinition]:
        stmt = select(BetEditPermission).where(
            BetEditPermission.bet_context_id == bet_context_id,
            BetEditPermission.starts_at <= now,
            BetEditPermission.ends_at > now,
            BetEditPermission.event_session_id.is_(None)
            if event_session_id is None
            else BetEditPermission.event_session_id == event_session_id,
            BetEditPermission.testing_event_session_id.is_(None)
            if testing_event_session_id is None
            else BetEditPermission.testing_event_session_id == testing_event_session_id,
        )

        permissions = self._session.execute(stmt).scalars().all()

        return [
            BetEditPermissionDefinition(
                applies_to_all=permission.applies_to_all,
                group_id=permission.group_id,
                user_id=permission.user_id,
                team_id=permission.team_id,
                starts_at=permission.starts_at,
                ends_at=permission.ends_at,
                max_modifications=permission.max_modifications,
            )
            for permission in permissions
        ]
    
    def upsert_user_bet_submission(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        answers: list[BetAnswerInput],
        submitted_at: datetime,
    ) -> None:
        stmt = (
            select(Bet)
            .where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
                Bet.event_session_id.is_(None)
                if event_session_id is None
                else Bet.event_session_id == event_session_id,
                Bet.testing_event_session_id.is_(None)
                if testing_event_session_id is None
                else Bet.testing_event_session_id == testing_event_session_id,
            )
            .options(
                selectinload(Bet.bet_picks),
                selectinload(Bet.submission_revisions),
            )
        )
        bet = self._session.execute(stmt).scalar_one_or_none()

        if bet is None:
            bet = Bet(
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
                submitted_at=submitted_at,
                last_modified_at=submitted_at,
                locked_at=None,
                submit_order_int=None,
            )
            self._session.add(bet)
            self._session.flush()
        else:
            if bet.submitted_at is None:
                bet.submitted_at = submitted_at

            bet.last_modified_at = submitted_at
            bet.locked_at = None
            bet.submit_order_int = None

        score_ids_by_code = self.get_bet_score_ids_by_codes(
            codes={answer.bet_score_code for answer in answers},
        )

        existing_picks_by_score_id = {
            pick.bet_score_id: pick
            for pick in bet.bet_picks
        }

        for answer in answers:
            bet_score_id = score_ids_by_code[answer.bet_score_code]
            existing_pick = existing_picks_by_score_id.get(bet_score_id)

            if existing_pick is None:
                self._session.add(
                    BetPick(
                        bet_id=bet.id,
                        bet_score_id=bet_score_id,
                        value=answer.value,
                    )
                )
            else:
                existing_pick.value = answer.value

        next_revision_number = len(bet.submission_revisions) + 1

        self._session.add(
            BetSubmissionRevision(
                bet_id=bet.id,
                revision_number=next_revision_number,
                submitted_at=submitted_at,
                reason=None,
            )
        )

        self._session.flush()
        self._session.expire(bet, ["bet_picks", "submission_revisions"])


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
            id=context.id,
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
