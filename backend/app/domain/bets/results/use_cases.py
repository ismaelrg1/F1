from datetime import datetime, timezone
from uuid import UUID

from app.db.enums import BetResultsVisibilityMode
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventResultsError,
    BetContextNotFoundForSeasonResultsError,
    BetContextNotFoundForTestingEventResultsError,
    RaceEventNotFoundForBetResultsError,
    RaceEventSessionNotFoundForBetResultsError,
    SeasonNotFoundForBetResultsError,
    TestingEventNotFoundForBetResultsError,
    TestingEventSessionNotFoundForBetResultsError,
)
from app.domain.bets.models import (
    # Results
    BetResultsScope,
    BetResultsVisibility,
    RaceEventBetResults,
    RaceEventBetResultsBlock,
    RaceEventBetResultsSession,
    RaceEventSessionBetResults,
    TestingEventSessionBetResults,
    SeasonBetResults,

    # Shared
    BetRaceEvent,
    BetRaceEventSession,
    BetTestingEvent,
    BetTestingEventSession,
    BetSeason,

)
from app.domain.bets.ports import BetResultsRepository # Results


class GetRaceEventBetResults:
    def __init__(self, repository: BetResultsRepository):
        self._repository = repository

    def execute(
        self,
        *,
        race_event_public_id: UUID,
        group_id: int,
        user_id: int,
    ) -> RaceEventBetResults:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise RaceEventNotFoundForBetResultsError()

        bet_context = self._repository.get_gp_bet_context(
            group_id=group_id,
            race_event_id=race_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForRaceEventResultsError()

        event_visibility = self._resolve_visibility(
            race_event=race_event,
            session=None,
            bet_context_id=bet_context.id,
            user_id=user_id,
        )

        event_entries = (
            self._repository.list_group_submitted_bet_entries(
                group_id=group_id,
                bet_context_id=bet_context.id,
                event_session_id=None,
                results_published=event_visibility.results_published,
            )
            if event_visibility.can_view_group_results
            else []
        )

        event_results = RaceEventBetResultsBlock(
            scope=BetResultsScope(
                type="EVENT",
                race_event_public_id=race_event.public_id,
                event_session_public_id=None,
                session_type=None,
            ),
            visibility=event_visibility,
            official_results=(
                self._repository.list_official_results(
                    bet_context_id=bet_context.id,
                    event_session_id=None,
                )
                if event_visibility.results_published
                else []
            ),
            entries=event_entries,
        )

        sessions: list[RaceEventBetResultsSession] = []
        for session in sorted(
            race_event.sessions,
            key=lambda item: (item.scheduled_start_datetime or item.start_datetime, item.id),
        ):
            session_visibility = self._resolve_visibility(
                race_event=race_event,
                session=session,
                bet_context_id=bet_context.id,
                user_id=user_id,
            )

            sessions.append(
                RaceEventBetResultsSession(
                    event_session_public_id=session.public_id,
                    session_type=session.session_type,
                    start_datetime=session.start_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    lock_cutoff=session.lock_cutoff,
                    scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                    status=session.status,
                    visibility=session_visibility,
                    official_results=(
                        self._repository.list_official_results(
                            bet_context_id=bet_context.id,
                            event_session_id=session.id,
                        )
                        if session_visibility.results_published
                        else []
                    ),
                    entries=(
                        self._repository.list_group_submitted_bet_entries(
                            group_id=group_id,
                            bet_context_id=bet_context.id,
                            event_session_id=session.id,
                            results_published=session_visibility.results_published,
                        )
                        if session_visibility.can_view_group_results
                        else []
                    ),
                )
            )

        return RaceEventBetResults(
            bet_context_public_id=bet_context.public_id,
            kind=bet_context.kind,
            race_event_public_id=race_event.public_id,
            label=bet_context.label,
            event_results=event_results,
            sessions=sessions,
        )

    def _resolve_visibility(
        self,
        *,
        race_event: BetRaceEvent,
        session: BetRaceEventSession | None,
        bet_context_id: int,
        user_id: int,
    ) -> BetResultsVisibility:
        now = datetime.now(timezone.utc)
        event_session_id = session.id if session is not None else None

        policy = self._repository.get_race_event_visibility(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            now=now,
        )

        viewer_submitted = self._repository.viewer_has_submitted_scope(
            user_id=user_id,
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
        )

        lock_cutoff = self._resolve_lock_cutoff(race_event=race_event, session=session)
        is_locked = lock_cutoff is not None and now >= lock_cutoff

        can_view = self._can_view(
            mode=policy.mode,
            viewer_submitted=viewer_submitted,
            is_locked=is_locked,
            results_published=policy.results_published,
        )

        return BetResultsVisibility(
            mode=policy.mode,
            can_view_group_results=can_view,
            reason=self._visibility_reason(
                mode=policy.mode,
                can_view=can_view,
                viewer_submitted=viewer_submitted,
                is_locked=is_locked,
                results_published=policy.results_published,
            ),
            is_locked=is_locked,
            results_published=policy.results_published,
            results_published_at=policy.results_published_at,
            viewer_submitted=viewer_submitted,
        )

    def _resolve_lock_cutoff(
        self,
        *,
        race_event: BetRaceEvent,
        session: BetRaceEventSession | None,
    ) -> datetime | None:
        if session is not None:
            return session.lock_cutoff or session.scheduled_lock_cutoff

        return (
            race_event.lock_cutoff
            or race_event.scheduled_lock_cutoff
            or race_event.event_start
            or race_event.scheduled_event_start
        )

    def _can_view(
        self,
        *,
        mode: BetResultsVisibilityMode,
        viewer_submitted: bool,
        is_locked: bool,
        results_published: bool,
    ) -> bool:
        if mode == BetResultsVisibilityMode.ALWAYS_VISIBLE:
            return True

        if mode == BetResultsVisibilityMode.SUBMIT_REQUIRED:
            return viewer_submitted or is_locked or results_published

        if mode == BetResultsVisibilityMode.AFTER_LOCK:
            return is_locked or results_published

        if mode == BetResultsVisibilityMode.AFTER_RESULTS_PUBLISHED:
            return results_published

        return False

    def _visibility_reason(
        self,
        *,
        mode: BetResultsVisibilityMode,
        can_view: bool,
        viewer_submitted: bool,
        is_locked: bool,
        results_published: bool,
    ) -> str:
        if can_view:
            if mode == BetResultsVisibilityMode.ALWAYS_VISIBLE:
                return "ALWAYS_VISIBLE"
            if results_published:
                return "RESULTS_PUBLISHED"
            if is_locked:
                return "LOCKED"
            if viewer_submitted:
                return "USER_SUBMITTED"
            return "VISIBLE"

        if mode == BetResultsVisibilityMode.SUBMIT_REQUIRED:
            return "SUBMIT_REQUIRED_NOT_SUBMITTED"

        if mode == BetResultsVisibilityMode.AFTER_LOCK:
            return "WAITING_FOR_LOCK"

        if mode == BetResultsVisibilityMode.AFTER_RESULTS_PUBLISHED:
            return "WAITING_FOR_RESULTS_PUBLICATION"

        return "NOT_VISIBLE"


class GetRaceEventSessionBetResults:
    def __init__(self, repository: BetResultsRepository):
        self._repository = repository
        self._race_event_use_case = GetRaceEventBetResults(repository)

    def execute(
        self,
        *,
        race_event_public_id: UUID,
        event_session_public_id: UUID,
        group_id: int,
        user_id: int,
    ) -> RaceEventSessionBetResults:
        full_result = self._race_event_use_case.execute(
            race_event_public_id=race_event_public_id,
            group_id=group_id,
            user_id=user_id,
        )

        session_result = next(
            (
                session
                for session in full_result.sessions
                if session.event_session_public_id == event_session_public_id
            ),
            None,
        )
        if session_result is None:
            raise RaceEventSessionNotFoundForBetResultsError()

        return RaceEventSessionBetResults(
            bet_context_public_id=full_result.bet_context_public_id,
            kind=full_result.kind,
            race_event_public_id=full_result.race_event_public_id,
            label=full_result.label,
            scope=BetResultsScope(
                type="SESSION",
                race_event_public_id=full_result.race_event_public_id,
                event_session_public_id=session_result.event_session_public_id,
                session_type=session_result.session_type,
            ),
            visibility=session_result.visibility,
            official_results=session_result.official_results,
            entries=session_result.entries,
        )
    
class GetTestingEventSessionBetResults:
    def __init__(self, repository: BetResultsRepository):
        self._repository = repository

    def execute(
        self,
        *,
        testing_event_public_id: UUID,
        testing_event_session_public_id: UUID,
        group_id: int,
        user_id: int,
    ) -> TestingEventSessionBetResults:
        testing_event = self._repository.get_testing_event_by_public_id(testing_event_public_id)
        if testing_event is None:
            raise TestingEventNotFoundForBetResultsError()

        session = next(
            (
                session
                for session in testing_event.sessions
                if session.public_id == testing_event_session_public_id
            ),
            None,
        )
        if session is None:
            raise TestingEventSessionNotFoundForBetResultsError()

        bet_context = self._repository.get_pretesting_bet_context(
            group_id=group_id,
            testing_event_id=testing_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForTestingEventResultsError()

        visibility = self._resolve_visibility(
            testing_event=testing_event,
            session=session,
            bet_context_id=bet_context.id,
            user_id=user_id,
        )

        return TestingEventSessionBetResults(
            bet_context_public_id=bet_context.public_id,
            kind=bet_context.kind,
            testing_event_public_id=testing_event.public_id,
            label=bet_context.label,
            scope=BetResultsScope(
                type="SESSION",
                testing_event_public_id=testing_event.public_id,
                testing_event_session_public_id=session.public_id,
                session_order=session.session_order,
                name=session.name,
            ),
            visibility=visibility,
            official_results=(
                self._repository.list_testing_official_results(
                    bet_context_id=bet_context.id,
                    testing_event_session_id=session.id,
                )
                if visibility.results_published
                else []
            ),
            entries=(
                self._repository.list_group_submitted_testing_bet_entries(
                    group_id=group_id,
                    bet_context_id=bet_context.id,
                    testing_event_session_id=session.id,
                    results_published=visibility.results_published,
                )
                if visibility.can_view_group_results
                else []
            ),
        )

    def _resolve_visibility(
        self,
        *,
        testing_event: BetTestingEvent,
        session: BetTestingEventSession | None,
        bet_context_id: int,
        user_id: int,
    ) -> BetResultsVisibility:
        now = datetime.now(timezone.utc)
        testing_event_session_id = session.id if session is not None else None

        policy = self._repository.get_testing_event_visibility(
            bet_context_id=bet_context_id,
            testing_event_session_id=testing_event_session_id,
            now=now,
        )

        viewer_submitted = self._repository.viewer_has_submitted_testing_scope(
            user_id=user_id,
            bet_context_id=bet_context_id,
            testing_event_session_id=testing_event_session_id,
        )

        lock_cutoff = self._resolve_lock_cutoff(
            testing_event=testing_event,
            session=session,
        )
        is_locked = lock_cutoff is not None and now >= lock_cutoff

        can_view = self._can_view(
            mode=policy.mode,
            viewer_submitted=viewer_submitted,
            is_locked=is_locked,
            results_published=policy.results_published,
        )

        return BetResultsVisibility(
            mode=policy.mode,
            can_view_group_results=can_view,
            reason=self._visibility_reason(
                mode=policy.mode,
                can_view=can_view,
                viewer_submitted=viewer_submitted,
                is_locked=is_locked,
                results_published=policy.results_published,
            ),
            is_locked=is_locked,
            results_published=policy.results_published,
            results_published_at=policy.results_published_at,
            viewer_submitted=viewer_submitted,
        )

    def _resolve_lock_cutoff(
        self,
        *,
        testing_event: BetTestingEvent,
        session: BetTestingEventSession | None,
    ) -> datetime | None:
        if session is not None:
            return session.lock_cutoff or session.scheduled_lock_cutoff

        return (
            testing_event.lock_cutoff
            or testing_event.scheduled_lock_cutoff
            or testing_event.event_start
            or testing_event.scheduled_event_start
        )

    def _can_view(
        self,
        *,
        mode: BetResultsVisibilityMode,
        viewer_submitted: bool,
        is_locked: bool,
        results_published: bool,
    ) -> bool:
        if mode == BetResultsVisibilityMode.ALWAYS_VISIBLE:
            return True

        if mode == BetResultsVisibilityMode.SUBMIT_REQUIRED:
            return viewer_submitted or is_locked or results_published

        if mode == BetResultsVisibilityMode.AFTER_LOCK:
            return is_locked or results_published

        if mode == BetResultsVisibilityMode.AFTER_RESULTS_PUBLISHED:
            return results_published

        return False

    def _visibility_reason(
        self,
        *,
        mode: BetResultsVisibilityMode,
        can_view: bool,
        viewer_submitted: bool,
        is_locked: bool,
        results_published: bool,
    ) -> str:
        if can_view:
            if mode == BetResultsVisibilityMode.ALWAYS_VISIBLE:
                return "ALWAYS_VISIBLE"
            if results_published:
                return "RESULTS_PUBLISHED"
            if is_locked:
                return "LOCKED"
            if viewer_submitted:
                return "USER_SUBMITTED"
            return "VISIBLE"

        if mode == BetResultsVisibilityMode.SUBMIT_REQUIRED:
            return "SUBMIT_REQUIRED_NOT_SUBMITTED"

        if mode == BetResultsVisibilityMode.AFTER_LOCK:
            return "WAITING_FOR_LOCK"

        if mode == BetResultsVisibilityMode.AFTER_RESULTS_PUBLISHED:
            return "WAITING_FOR_RESULTS_PUBLICATION"

        return "NOT_VISIBLE"
    

class GetSeasonBetResults:
    def __init__(self, repository: BetResultsRepository):
        self._repository = repository

    def execute(
        self,
        *,
        season_year: int,
        group_id: int,
        user_id: int,
    ) -> SeasonBetResults:
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForBetResultsError()

        bet_context = self._repository.get_season_bet_context(
            group_id=group_id,
            season_id=season.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForSeasonResultsError()

        visibility = self._resolve_visibility(
            season=season,
            bet_context_id=bet_context.id,
            user_id=user_id,
        )

        return SeasonBetResults(
            bet_context_public_id=bet_context.public_id,
            kind=bet_context.kind,
            season_year=season.year,
            label=bet_context.label,
            scope=BetResultsScope(
                type="SEASON",
                season_year=season.year,
            ),
            visibility=visibility,
            official_results=(
                self._repository.list_season_official_results(
                    bet_context_id=bet_context.id,
                )
                if visibility.results_published
                else []
            ),
            entries=(
                self._repository.list_group_submitted_season_bet_entries(
                    group_id=group_id,
                    bet_context_id=bet_context.id,
                    results_published=visibility.results_published,
                )
                if visibility.can_view_group_results
                else []
            ),
        )

    def _resolve_visibility(
        self,
        *,
        season: BetSeason,
        bet_context_id: int,
        user_id: int,
    ) -> BetResultsVisibility:
        now = datetime.now(timezone.utc)

        policy = self._repository.get_season_visibility(
            bet_context_id=bet_context_id,
            now=now,
        )

        viewer_submitted = self._repository.viewer_has_submitted_season_scope(
            user_id=user_id,
            bet_context_id=bet_context_id,
        )

        lock_cutoff = self._resolve_lock_cutoff(season=season)
        is_locked = lock_cutoff is not None and now >= lock_cutoff

        can_view = self._can_view(
            mode=policy.mode,
            viewer_submitted=viewer_submitted,
            is_locked=is_locked,
            results_published=policy.results_published,
        )

        return BetResultsVisibility(
            mode=policy.mode,
            can_view_group_results=can_view,
            reason=self._visibility_reason(
                mode=policy.mode,
                can_view=can_view,
                viewer_submitted=viewer_submitted,
                is_locked=is_locked,
                results_published=policy.results_published,
            ),
            is_locked=is_locked,
            results_published=policy.results_published,
            results_published_at=policy.results_published_at,
            viewer_submitted=viewer_submitted,
        )

    def _resolve_lock_cutoff(self, *, season: BetSeason) -> datetime | None:
        return season.lock_cutoff or season.scheduled_lock_cutoff

    def _can_view(
        self,
        *,
        mode: BetResultsVisibilityMode,
        viewer_submitted: bool,
        is_locked: bool,
        results_published: bool,
    ) -> bool:
        if mode == BetResultsVisibilityMode.ALWAYS_VISIBLE:
            return True

        if mode == BetResultsVisibilityMode.SUBMIT_REQUIRED:
            return viewer_submitted or is_locked or results_published

        if mode == BetResultsVisibilityMode.AFTER_LOCK:
            return is_locked or results_published

        if mode == BetResultsVisibilityMode.AFTER_RESULTS_PUBLISHED:
            return results_published

        return False

    def _visibility_reason(
        self,
        *,
        mode: BetResultsVisibilityMode,
        can_view: bool,
        viewer_submitted: bool,
        is_locked: bool,
        results_published: bool,
    ) -> str:
        if can_view:
            if mode == BetResultsVisibilityMode.ALWAYS_VISIBLE:
                return "ALWAYS_VISIBLE"
            if results_published:
                return "RESULTS_PUBLISHED"
            if is_locked:
                return "LOCKED"
            if viewer_submitted:
                return "USER_SUBMITTED"
            return "VISIBLE"

        if mode == BetResultsVisibilityMode.SUBMIT_REQUIRED:
            return "SUBMIT_REQUIRED_NOT_SUBMITTED"

        if mode == BetResultsVisibilityMode.AFTER_LOCK:
            return "WAITING_FOR_LOCK"

        if mode == BetResultsVisibilityMode.AFTER_RESULTS_PUBLISHED:
            return "WAITING_FOR_RESULTS_PUBLICATION"

        return "NOT_VISIBLE"