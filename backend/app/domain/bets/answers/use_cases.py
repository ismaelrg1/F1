from uuid import UUID
from datetime import datetime, timezone

from app.domain.bets.enums import BetTemplateScope
from app.domain.bets.shared.ports import BetQuestionsRepository
from app.domain.bets.shared.models import (
    BetRaceEvent,
    BetRaceEventSession,
    BetTemplateDefinition,
    BetExceptionDefinition,
)
from app.domain.bets.answers.models import (
    RaceEventBetAnswersResult,
    RaceEventBetAnswersSessionResult,
    SeasonBetAnswersResult,
    TestingEventBetAnswersResult,
    TestingEventBetAnswersSessionResult,
    BetAnswerInput,
)
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    BetContextNotFoundForSeasonError,
    BetContextNotFoundForTestingEventError,
    RaceEventNotFoundForBetQuestionsError,
    RaceEventSessionNotFoundForBetAnswersError,
    SeasonNotFoundForBetQuestionsError,
    TestingEventNotFoundForBetQuestionsError,
    TestingEventSessionNotFoundForBetAnswersError,
    BetAlreadySubmittedError,
    BetAnswerQuestionNotFoundError,
    BetAnswersClosedError,
    BetAnswersNotOpenError,
)


class GetRaceEventBetAnswers:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(self, *, race_event_public_id: UUID, group_id: int, user_id: int) -> RaceEventBetAnswersResult:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise RaceEventNotFoundForBetQuestionsError()

        bet_context = self._repository.get_gp_bet_context(
            group_id=group_id,
            race_event_id=race_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForRaceEventError()

        bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        event_bet = next((bet for bet in bets if bet.event_session_id is None), None)
        session_bets_by_id = {
            bet.event_session_id: bet
            for bet in bets
            if bet.event_session_id is not None
        }

        sessions: list[RaceEventBetAnswersSessionResult] = []
        for session in sorted(
            race_event.sessions,
            key=lambda s: (s.scheduled_start_datetime or s.start_datetime, s.id),
        ):
            session_bet = session_bets_by_id.get(session.id)

            sessions.append(
                RaceEventBetAnswersSessionResult(
                    event_session_public_id=session.public_id,
                    session_type=session.session_type,
                    submitted_at=session_bet.submitted_at if session_bet is not None else None,
                    last_modified_at=session_bet.last_modified_at if session_bet is not None else None,
                    locked_at=session_bet.locked_at if session_bet is not None else None,
                    answers=list(session_bet.picks) if session_bet is not None else [],
                )
            )

        return RaceEventBetAnswersResult(
            bet_context_public_id=bet_context.public_id,
            kind=str(bet_context.kind),
            race_event_public_id=race_event.public_id,
            label=bet_context.label,
            submitted_at=event_bet.submitted_at if event_bet is not None else None,
            last_modified_at=event_bet.last_modified_at if event_bet is not None else None,
            locked_at=event_bet.locked_at if event_bet is not None else None,
            event_answers=list(event_bet.picks) if event_bet is not None else [],
            sessions=sessions,
        )
        

class GetRaceEventSessionBetAnswers:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(
        self,
        *,
        race_event_public_id: UUID,
        event_session_public_id: UUID,
        group_id: int,
        user_id: int,
    ) -> RaceEventBetAnswersResult:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise RaceEventNotFoundForBetQuestionsError()

        session = next(
            (
                session
                for session in race_event.sessions
                if session.public_id == event_session_public_id
            ),
            None,
        )
        if session is None:
            raise RaceEventSessionNotFoundForBetAnswersError()

        bet_context = self._repository.get_gp_bet_context(
            group_id=group_id,
            race_event_id=race_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForRaceEventError()

        bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        session_bet = next(
            (
                bet
                for bet in bets
                if bet.event_session_id == session.id
            ),
            None,
        )

        return RaceEventBetAnswersResult(
            bet_context_public_id=bet_context.public_id,
            kind=str(bet_context.kind),
            race_event_public_id=race_event.public_id,
            label=bet_context.label,
            submitted_at=None,
            last_modified_at=None,
            locked_at=None,
            event_answers=[],
            sessions=[
                RaceEventBetAnswersSessionResult(
                    event_session_public_id=session.public_id,
                    session_type=session.session_type,
                    submitted_at=session_bet.submitted_at if session_bet is not None else None,
                    last_modified_at=session_bet.last_modified_at if session_bet is not None else None,
                    locked_at=session_bet.locked_at if session_bet is not None else None,
                    answers=list(session_bet.picks) if session_bet is not None else [],
                )
            ],
        )
    
class GetTestingEventBetAnswers:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(self, *, testing_event_public_id: UUID, group_id: int, user_id: int) -> TestingEventBetAnswersResult:
        testing_event = self._repository.get_testing_event_by_public_id(testing_event_public_id)
        if testing_event is None:
            raise TestingEventNotFoundForBetQuestionsError()

        bet_context = self._repository.get_pretesting_bet_context(
            group_id=group_id,
            testing_event_id=testing_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForTestingEventError()

        bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        event_bet = next(
            (
                bet
                for bet in bets
                if bet.event_session_id is None and bet.testing_event_session_id is None
            ),
            None,
        )

        session_bets_by_id = {
            bet.testing_event_session_id: bet
            for bet in bets
            if bet.testing_event_session_id is not None
        }

        sessions: list[TestingEventBetAnswersSessionResult] = []
        for session in sorted(testing_event.sessions, key=lambda s: (s.session_order, s.id)):
            session_bet = session_bets_by_id.get(session.id)

            sessions.append(
                TestingEventBetAnswersSessionResult(
                    testing_event_session_public_id=session.public_id,
                    session_order=session.session_order,
                    name=session.name,
                    submitted_at=session_bet.submitted_at if session_bet is not None else None,
                    last_modified_at=session_bet.last_modified_at if session_bet is not None else None,
                    locked_at=session_bet.locked_at if session_bet is not None else None,
                    answers=list(session_bet.picks) if session_bet is not None else [],
                )
            )

        return TestingEventBetAnswersResult(
            bet_context_public_id=bet_context.public_id,
            kind=str(bet_context.kind),
            testing_event_public_id=testing_event.public_id,
            label=bet_context.label,
            status=testing_event.status,
            submitted_at=event_bet.submitted_at if event_bet is not None else None,
            last_modified_at=event_bet.last_modified_at if event_bet is not None else None,
            locked_at=event_bet.locked_at if event_bet is not None else None,
            event_answers=list(event_bet.picks) if event_bet is not None else [],
            sessions=sessions,
        )


class GetTestingEventSessionBetAnswers:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(
        self,
        *,
        testing_event_public_id: UUID,
        testing_event_session_public_id: UUID,
        group_id: int,
        user_id: int,
    ) -> TestingEventBetAnswersResult:
        testing_event = self._repository.get_testing_event_by_public_id(testing_event_public_id)
        if testing_event is None:
            raise TestingEventNotFoundForBetQuestionsError()

        session = next(
            (
                session
                for session in testing_event.sessions
                if session.public_id == testing_event_session_public_id
            ),
            None,
        )
        if session is None:
            raise TestingEventSessionNotFoundForBetAnswersError()

        bet_context = self._repository.get_pretesting_bet_context(
            group_id=group_id,
            testing_event_id=testing_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForTestingEventError()

        bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        session_bet = next(
            (
                bet
                for bet in bets
                if bet.testing_event_session_id == session.id
            ),
            None,
        )

        return TestingEventBetAnswersResult(
            bet_context_public_id=bet_context.public_id,
            kind=str(bet_context.kind),
            testing_event_public_id=testing_event.public_id,
            label=bet_context.label,
            status=testing_event.status,
            submitted_at=None,
            last_modified_at=None,
            locked_at=None,
            event_answers=[],
            sessions=[
                TestingEventBetAnswersSessionResult(
                    testing_event_session_public_id=session.public_id,
                    session_order=session.session_order,
                    name=session.name,
                    submitted_at=session_bet.submitted_at if session_bet is not None else None,
                    last_modified_at=session_bet.last_modified_at if session_bet is not None else None,
                    locked_at=session_bet.locked_at if session_bet is not None else None,
                    answers=list(session_bet.picks) if session_bet is not None else [],
                )
            ],
        )


class GetSeasonBetAnswers:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(self, *, season_year: int, group_id: int, user_id: int) -> SeasonBetAnswersResult:
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForBetQuestionsError()

        bet_context = self._repository.get_season_bet_context(
            group_id=group_id,
            season_id=season.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForSeasonError()

        bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        season_bet = next(
            (
                bet
                for bet in bets
                if bet.event_session_id is None and bet.testing_event_session_id is None
            ),
            None,
        )

        return SeasonBetAnswersResult(
            bet_context_public_id=bet_context.public_id,
            kind=str(bet_context.kind),
            season_year=season.year,
            label=bet_context.label,
            submitted_at=season_bet.submitted_at if season_bet is not None else None,
            last_modified_at=season_bet.last_modified_at if season_bet is not None else None,
            locked_at=season_bet.locked_at if season_bet is not None else None,
            answers=list(season_bet.picks) if season_bet is not None else [],
        )
    
class PatchRaceEventBetAnswers:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(
        self,
        *,
        race_event_public_id: UUID,
        event_session_public_id: UUID | None,
        group_id: int,
        user_id: int,
        answers: list[BetAnswerInput],
    ) -> RaceEventBetAnswersResult:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise RaceEventNotFoundForBetQuestionsError()

        session = None
        if event_session_public_id is not None:
            session = next(
                (
                    session
                    for session in race_event.sessions
                    if session.public_id == event_session_public_id
                ),
                None,
            )
            if session is None:
                raise RaceEventSessionNotFoundForBetAnswersError()

        bet_context = self._repository.get_gp_bet_context(
            group_id=group_id,
            race_event_id=race_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForRaceEventError()

        now = datetime.now(timezone.utc)

        betting_open_at, lock_cutoff = self._resolve_betting_window(
            race_event=race_event,
            session=session,
        )

        if betting_open_at is not None and now < betting_open_at:
            raise BetAnswersNotOpenError()

        if lock_cutoff is not None and now >= lock_cutoff:
            raise BetAnswersClosedError()

        templates = self._repository.list_gp_templates_for_season(
            season_id=race_event.season_id,
        )

        allowed_score_codes = self._resolve_allowed_score_codes(
            templates=templates,
            bet_context_exceptions=bet_context.exceptions,
            session=session,
        )

        received_codes = {
            answer.bet_score_code
            for answer in answers
        }

        if not received_codes.issubset(allowed_score_codes):
            raise BetAnswerQuestionNotFoundError()

        score_ids_by_code = self._repository.get_bet_score_ids_by_codes(
            codes=received_codes,
        )
        if set(score_ids_by_code) != received_codes:
            raise BetAnswerQuestionNotFoundError()

        existing_bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        current_bet = next(
            (
                bet
                for bet in existing_bets
                if bet.event_session_id == (session.id if session is not None else None)
                and bet.testing_event_session_id is None
            ),
            None,
        )

        if current_bet is not None and current_bet.submitted_at is not None:
            raise BetAlreadySubmittedError()

        self._repository.upsert_user_bet_draft(
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=session.id if session is not None else None,
            testing_event_session_id=None,
            answers=answers,
            modified_at=now,
        )

        if session is not None:
            return GetRaceEventSessionBetAnswers(self._repository).execute(
                race_event_public_id=race_event_public_id,
                event_session_public_id=event_session_public_id,
                group_id=group_id,
                user_id=user_id,
            )

        return GetRaceEventBetAnswers(self._repository).execute(
            race_event_public_id=race_event_public_id,
            group_id=group_id,
            user_id=user_id,
        )

    def _resolve_betting_window(
        self,
        *,
        race_event: BetRaceEvent,
        session: BetRaceEventSession | None,
    ) -> tuple[datetime | None, datetime | None]:
        if session is not None:
            betting_open_at = session.betting_open_at
            lock_cutoff = session.lock_cutoff or session.scheduled_lock_cutoff
            return betting_open_at, lock_cutoff

        betting_open_at = race_event.betting_open_at
        lock_cutoff = (
            race_event.lock_cutoff
            or race_event.scheduled_lock_cutoff
            or race_event.event_start
            or race_event.scheduled_event_start
        )
        return betting_open_at, lock_cutoff

    def _resolve_allowed_score_codes(
        self,
        *,
        templates: list[BetTemplateDefinition],
        bet_context_exceptions: tuple[BetExceptionDefinition, ...],
        session: BetRaceEventSession | None,
    ) -> set[str]:
        if session is None:
            template_scope = BetTemplateScope.EVENT
            template_session_type = None
            exception_event_session_id = None
        else:
            template_scope = BetTemplateScope.SESSION
            template_session_type = session.session_type
            exception_event_session_id = session.id

        allowed_codes: set[str] = set()
        score_id_by_code: dict[str, int] = {}

        for template in templates:
            if template.scope != template_scope:
                continue

            if template_session_type is not None and template.session_type != template_session_type:
                continue

            for item in template.items:
                allowed_codes.add(item.bet_score.code)
                score_id_by_code[item.bet_score.code] = item.bet_score.id

        disabled_score_ids = {
            exception.bet_score_id
            for exception in bet_context_exceptions
            if exception.event_session_id == exception_event_session_id
            and exception.is_disabled is True
        }

        fallback_disabled_score_ids = set()
        if session is not None:
            fallback_disabled_score_ids = {
                exception.bet_score_id
                for exception in bet_context_exceptions
                if exception.event_session_id is None
                and exception.is_disabled is True
            }

        disabled_score_ids = disabled_score_ids | fallback_disabled_score_ids

        return {
            code
            for code in allowed_codes
            if score_id_by_code[code] not in disabled_score_ids
        }
