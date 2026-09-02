from uuid import UUID
from datetime import datetime, timezone

from app.domain.bets.enums import BetTemplateScope
from app.domain.bets.ports import BetAnswersRepository
from app.domain.bets.models import (
    # Shared
    BetRaceEvent,
    BetRaceEventSession,
    BetTemplateDefinition,
    BetExceptionDefinition,
    BetTestingEventSession,
    BetTestingEvent,
    BetSeason,
    BetEditPermissionDefinition,

    # Answers
    RaceEventBetAnswersResult,
    RaceEventBetAnswersSessionResult,
    SeasonBetAnswersResult,
    TestingEventBetAnswersResult,
    TestingEventBetAnswersSessionResult,
    BetAnswerInput,
    BetAnswerResult,
)
from app.domain.bets.answers.models import (
    BetPowerUpUseInput,
    BetPowerUpAssignmentDefinition,
    BetPowerUpTargetInput,
    ResolvedBetPowerUpTarget,
    ResolvedBetPowerUpUse,
)
from app.domain.bets.answers.validators import BetAnswerRelationsValidator
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    BetContextNotFoundForSeasonError,
    BetContextNotFoundForTestingEventError,
    RaceEventNotFoundForBetAnswersError,
    RaceEventSessionNotFoundForBetAnswersError,
    SeasonNotFoundForBetAnswersError,
    TestingEventNotFoundForBetAnswersError,
    TestingEventSessionNotFoundForBetAnswersError,
    BetAlreadySubmittedError,
    BetAnswerQuestionNotFoundError,
    BetAnswersClosedError,
    BetAnswersNotOpenError,
    BetModificationLimitReachedError,
    BetRequiredAnswerMissingError,
    BetPowerUpsCannotBeUsedAfterSubmitError,

    BetPowerUpAlreadyUsedError,
    BetPowerUpDisabledError,
    BetPowerUpNotAssignedError,
    BetPowerUpPenaltyLimitReachedError,
    BetPowerUpRestrictedError,
    BetPowerUpTargetNotAllowedError,
    BetPowerUpTargetRequiredError,
)

def _validate_answer_relations(
    *,
    repository: BetAnswersRepository,
    allowed_score_codes: set[str],
    existing_answers: tuple[BetAnswerResult, ...],
    received_answers: list[BetAnswerInput],
) -> None:
    relations = repository.list_bet_score_relations_for_codes(
        codes=allowed_score_codes,
    )

    BetAnswerRelationsValidator().validate(
        allowed_score_codes=allowed_score_codes,
        existing_answers=existing_answers,
        received_answers=received_answers,
        relations=relations,
    )

class GetRaceEventBetAnswers:
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(self, *, race_event_public_id: UUID, group_id: int, user_id: int) -> RaceEventBetAnswersResult:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise RaceEventNotFoundForBetAnswersError()

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
    def __init__(self, repository: BetAnswersRepository):
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
            raise RaceEventNotFoundForBetAnswersError()

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
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(self, *, testing_event_public_id: UUID, group_id: int, user_id: int) -> TestingEventBetAnswersResult:
        testing_event = self._repository.get_testing_event_by_public_id(testing_event_public_id)
        if testing_event is None:
            raise TestingEventNotFoundForBetAnswersError()

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
    def __init__(self, repository: BetAnswersRepository):
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
            raise TestingEventNotFoundForBetAnswersError()

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
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(self, *, season_year: int, group_id: int, user_id: int) -> SeasonBetAnswersResult:
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForBetAnswersError()


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
    def __init__(self, repository: BetAnswersRepository):
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
            raise RaceEventNotFoundForBetAnswersError()

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

        _validate_answer_relations(
            repository=self._repository,
            allowed_score_codes=allowed_score_codes,
            existing_answers=current_bet.picks if current_bet is not None else (),
            received_answers=answers,
        )

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


class PatchTestingEventBetAnswers:
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(
        self,
        *,
        testing_event_public_id: UUID,
        testing_event_session_public_id: UUID | None,
        group_id: int,
        user_id: int,
        answers: list[BetAnswerInput],
    ) -> TestingEventBetAnswersResult:
        testing_event = self._repository.get_testing_event_by_public_id(
            testing_event_public_id
        )
        if testing_event is None:
            raise TestingEventNotFoundForBetAnswersError()

        session = None
        if testing_event_session_public_id is not None:
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

        now = datetime.now(timezone.utc)

        betting_open_at, lock_cutoff = self._resolve_betting_window(
            testing_event=testing_event,
            session=session,
        )

        if betting_open_at is not None and now < betting_open_at:
            raise BetAnswersNotOpenError()

        if lock_cutoff is not None and now >= lock_cutoff:
            raise BetAnswersClosedError()

        templates = self._repository.list_pretesting_templates_for_season(
            season_id=testing_event.season_id,
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
                if bet.event_session_id is None
                and bet.testing_event_session_id == (session.id if session is not None else None)
            ),
            None,
        )

        if current_bet is not None and current_bet.submitted_at is not None:
            raise BetAlreadySubmittedError()

        _validate_answer_relations(
            repository=self._repository,
            allowed_score_codes=allowed_score_codes,
            existing_answers=current_bet.picks if current_bet is not None else (),
            received_answers=answers,
        )

        self._repository.upsert_user_bet_draft(
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=None,
            testing_event_session_id=session.id if session is not None else None,
            answers=answers,
            modified_at=now,
        )

        if session is not None:
            return GetTestingEventSessionBetAnswers(self._repository).execute(
                testing_event_public_id=testing_event_public_id,
                testing_event_session_public_id=testing_event_session_public_id,
                group_id=group_id,
                user_id=user_id,
            )

        return GetTestingEventBetAnswers(self._repository).execute(
            testing_event_public_id=testing_event_public_id,
            group_id=group_id,
            user_id=user_id,
        )

    def _resolve_betting_window(
        self,
        *,
        testing_event: BetTestingEvent,
        session: BetTestingEventSession | None,
    ) -> tuple[datetime | None, datetime | None]:
        if session is not None:
            betting_open_at = session.betting_open_at
            lock_cutoff = session.lock_cutoff or session.scheduled_lock_cutoff
            return betting_open_at, lock_cutoff

        betting_open_at = testing_event.betting_open_at
        lock_cutoff = (
            testing_event.lock_cutoff
            or testing_event.scheduled_lock_cutoff
            or testing_event.event_start
            or testing_event.scheduled_event_start
        )
        return betting_open_at, lock_cutoff

    def _resolve_allowed_score_codes(
        self,
        *,
        templates: list[BetTemplateDefinition],
        bet_context_exceptions: tuple[BetExceptionDefinition, ...],
        session: BetTestingEventSession | None,
    ) -> set[str]:
        allowed_codes: set[str] = set()
        score_id_by_code: dict[str, int] = {}

        for template in templates:
            if template.scope != BetTemplateScope.EVENT:
                continue

            for item in template.items:
                allowed_codes.add(item.bet_score.code)
                score_id_by_code[item.bet_score.code] = item.bet_score.id

        disabled_score_ids = {
            exception.bet_score_id
            for exception in bet_context_exceptions
            if exception.event_session_id is None
            and exception.is_disabled is True
        }

        return {
            code
            for code in allowed_codes
            if score_id_by_code[code] not in disabled_score_ids
        }



class PatchSeasonBetAnswers:
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(
        self,
        *,
        season_year: int,
        group_id: int,
        user_id: int,
        answers: list[BetAnswerInput],
    ) -> SeasonBetAnswersResult:
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForBetAnswersError()


        bet_context = self._repository.get_season_bet_context(
            group_id=group_id,
            season_id=season.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForSeasonError()

        now = datetime.now(timezone.utc)

        betting_open_at, lock_cutoff = self._resolve_betting_window(season=season)

        if betting_open_at is not None and now < betting_open_at:
            raise BetAnswersNotOpenError()

        if lock_cutoff is not None and now >= lock_cutoff:
            raise BetAnswersClosedError()

        templates = self._repository.list_season_templates_for_season(
            season_id=season.id,
        )

        allowed_score_codes = self._resolve_allowed_score_codes(
            templates=templates,
            bet_context_exceptions=bet_context.exceptions,
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
                if bet.event_session_id is None
                and bet.testing_event_session_id is None
            ),
            None,
        )

        if current_bet is not None and current_bet.submitted_at is not None:
            raise BetAlreadySubmittedError()

        _validate_answer_relations(
            repository=self._repository,
            allowed_score_codes=allowed_score_codes,
            existing_answers=current_bet.picks if current_bet is not None else (),
            received_answers=answers,
        )

        self._repository.upsert_user_bet_draft(
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=None,
            testing_event_session_id=None,
            answers=answers,
            modified_at=now,
        )

        return GetSeasonBetAnswers(self._repository).execute(
            season_year=season_year,
            group_id=group_id,
            user_id=user_id,
        )

    def _resolve_betting_window(
        self,
        *,
        season: BetSeason,
    ) -> tuple[datetime | None, datetime | None]:
        betting_open_at = season.betting_open_at
        lock_cutoff = season.lock_cutoff or season.scheduled_lock_cutoff
        return betting_open_at, lock_cutoff

    def _resolve_allowed_score_codes(
        self,
        *,
        templates: list[BetTemplateDefinition],
        bet_context_exceptions: tuple[BetExceptionDefinition, ...],
    ) -> set[str]:
        allowed_codes: set[str] = set()
        score_id_by_code: dict[str, int] = {}

        for template in templates:
            if template.scope != BetTemplateScope.EVENT:
                continue

            for item in template.items:
                allowed_codes.add(item.bet_score.code)
                score_id_by_code[item.bet_score.code] = item.bet_score.id

        disabled_score_ids = {
            exception.bet_score_id
            for exception in bet_context_exceptions
            if exception.event_session_id is None
            and exception.is_disabled is True
        }

        return {
            code
            for code in allowed_codes
            if score_id_by_code[code] not in disabled_score_ids
        }

class SubmitRaceEventBetAnswers:
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(
        self,
        *,
        race_event_public_id: UUID,
        event_session_public_id: UUID | None,
        group_id: int,
        user_id: int,
        team_ids: set[int],
        answers: list[BetAnswerInput],
        powerups: list[BetPowerUpUseInput],
    ) -> RaceEventBetAnswersResult:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise RaceEventNotFoundForBetAnswersError()

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

        existing_bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        if powerups and self._repository.user_has_any_submitted_bet_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        ):
            raise BetPowerUpsCannotBeUsedAfterSubmitError()

        current_bet = next(
            (
                bet
                for bet in existing_bets
                if bet.event_session_id == (session.id if session is not None else None)
                and bet.testing_event_session_id is None
            ),
            None,
        )

        if current_bet is not None and current_bet.locked_at is not None:
            raise BetAnswersClosedError()

        is_modification = current_bet is not None and current_bet.submitted_at is not None

        betting_open_at, lock_cutoff = self._resolve_betting_window(
            race_event=race_event,
            session=session,
        )

        has_normal_window = self._normal_window_is_open(
            now=now,
            betting_open_at=betting_open_at,
            lock_cutoff=lock_cutoff,
        )

        matching_permission = None
        if not has_normal_window and is_modification:
            matching_permission = self._find_matching_edit_permission(
                permissions=self._repository.list_active_edit_permissions_for_scope(
                    bet_context_id=bet_context.id,
                    event_session_id=session.id if session is not None else None,
                    testing_event_session_id=None,
                    now=now,
                ),
                group_id=group_id,
                user_id=user_id,
                team_ids=team_ids,
            )

        if not has_normal_window and matching_permission is None:
            if betting_open_at is not None and now < betting_open_at:
                raise BetAnswersNotOpenError()
            raise BetAnswersClosedError()

        max_modifications = matching_permission.max_modifications if matching_permission is not None else None
        if is_modification and max_modifications is not None:
            modification_count = max(current_bet.revision_count - 1, 0)
            if modification_count >= max_modifications:
                raise BetModificationLimitReachedError()

        templates = self._repository.list_gp_templates_for_season(
            season_id=race_event.season_id,
        )

        allowed_score_codes, required_score_codes = self._resolve_allowed_and_required_score_codes(
            templates=templates,
            bet_context_exceptions=bet_context.exceptions,
            session=session,
        )

        answers_by_code = {
            answer.bet_score_code: answer
            for answer in answers
        }

        existing_answers_by_code = {}
        if current_bet is not None:
            existing_answers_by_code = {
                pick.bet_score_code: pick
                for pick in current_bet.picks
            }

        received_codes = set(answers_by_code)
        existing_codes = set(existing_answers_by_code)
        final_answer_codes = received_codes | existing_codes

        if not received_codes.issubset(allowed_score_codes):
            raise BetAnswerQuestionNotFoundError()

        if not required_score_codes.issubset(final_answer_codes):
            raise BetRequiredAnswerMissingError()

        score_ids_by_code = self._repository.get_bet_score_ids_by_codes(
            codes=received_codes,
        )
        if set(score_ids_by_code) != received_codes:
            raise BetAnswerQuestionNotFoundError()

        _validate_answer_relations(
            repository=self._repository,
            allowed_score_codes=allowed_score_codes,
            existing_answers=current_bet.picks if current_bet is not None else (),
            received_answers=answers,
        )

        resolved_powerups = BetPowerUpSubmissionValidator(self._repository).resolve(
            group_id=group_id,
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=session.id if session is not None else None,
            testing_event_session_id=None,
            powerups=powerups,
        )

        self._repository.upsert_user_bet_submission(
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=session.id if session is not None else None,
            testing_event_session_id=None,
            answers=answers,
            submitted_at=now,
        )

        if resolved_powerups:
            self._repository.create_powerup_uses_for_submission(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context.id,
                event_session_id=session.id if session is not None else None,
                testing_event_session_id=None,
                powerups=resolved_powerups,
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

    def _normal_window_is_open(
        self,
        *,
        now: datetime,
        betting_open_at: datetime | None,
        lock_cutoff: datetime | None,
    ) -> bool:
        if betting_open_at is not None and now < betting_open_at:
            return False
        if lock_cutoff is not None and now >= lock_cutoff:
            return False
        return True

    def _find_matching_edit_permission(
        self,
        *,
        permissions: list[BetEditPermissionDefinition],
        group_id: int,
        user_id: int,
        team_ids: set[int],
    ) -> BetEditPermissionDefinition | None:
        for permission in permissions:
            if permission.applies_to_all:
                return permission
            if permission.group_id == group_id:
                return permission
            if permission.user_id == user_id:
                return permission
            if permission.team_id is not None and permission.team_id in team_ids:
                return permission

        return None

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

    def _resolve_allowed_and_required_score_codes(
        self,
        *,
        templates: list[BetTemplateDefinition],
        bet_context_exceptions: tuple[BetExceptionDefinition, ...],
        session: BetRaceEventSession | None,
    ) -> tuple[set[str], set[str]]:
        if session is None:
            template_scope = BetTemplateScope.EVENT
            template_session_type = None
            exception_event_session_id = None
        else:
            template_scope = BetTemplateScope.SESSION
            template_session_type = session.session_type
            exception_event_session_id = session.id

        allowed_codes: set[str] = set()
        required_codes: set[str] = set()
        score_id_by_code: dict[str, int] = {}

        for template in templates:
            if template.scope != template_scope:
                continue

            if template_session_type is not None and template.session_type != template_session_type:
                continue

            for item in template.items:
                allowed_codes.add(item.bet_score.code)
                score_id_by_code[item.bet_score.code] = item.bet_score.id

                if item.required is True:
                    required_codes.add(item.bet_score.code)

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

        allowed_codes = {
            code
            for code in allowed_codes
            if score_id_by_code[code] not in disabled_score_ids
        }

        required_codes = {
            code
            for code in required_codes
            if score_id_by_code[code] not in disabled_score_ids
        }

        return allowed_codes, required_codes


class SubmitTestingEventBetAnswers:
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(
        self,
        *,
        testing_event_public_id: UUID,
        testing_event_session_public_id: UUID | None,
        group_id: int,
        user_id: int,
        team_ids: set[int],
        answers: list[BetAnswerInput],
        powerups: list[BetPowerUpUseInput],
    ) -> TestingEventBetAnswersResult:
        testing_event = self._repository.get_testing_event_by_public_id(
            testing_event_public_id
        )
        if testing_event is None:
            raise TestingEventNotFoundForBetAnswersError()

        session = None
        if testing_event_session_public_id is not None:
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

        now = datetime.now(timezone.utc)

        existing_bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        if powerups and self._repository.user_has_any_submitted_bet_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        ):
            raise BetPowerUpsCannotBeUsedAfterSubmitError()

        current_bet = next(
            (
                bet
                for bet in existing_bets
                if bet.event_session_id is None
                and bet.testing_event_session_id == (session.id if session is not None else None)
            ),
            None,
        )

        if current_bet is not None and current_bet.locked_at is not None:
            raise BetAnswersClosedError()

        is_modification = current_bet is not None and current_bet.submitted_at is not None

        betting_open_at, lock_cutoff = self._resolve_betting_window(
            testing_event=testing_event,
            session=session,
        )

        has_normal_window = self._normal_window_is_open(
            now=now,
            betting_open_at=betting_open_at,
            lock_cutoff=lock_cutoff,
        )

        matching_permission = None
        if not has_normal_window and is_modification:
            matching_permission = self._find_matching_edit_permission(
                permissions=self._repository.list_active_edit_permissions_for_scope(
                    bet_context_id=bet_context.id,
                    event_session_id=None,
                    testing_event_session_id=session.id if session is not None else None,
                    now=now,
                ),
                group_id=group_id,
                user_id=user_id,
                team_ids=team_ids,
            )

        if not has_normal_window and matching_permission is None:
            if betting_open_at is not None and now < betting_open_at:
                raise BetAnswersNotOpenError()
            raise BetAnswersClosedError()

        max_modifications = (
            matching_permission.max_modifications
            if matching_permission is not None
            else None
        )
        if is_modification and max_modifications is not None:
            modification_count = max(current_bet.revision_count - 1, 0)
            if modification_count >= max_modifications:
                raise BetModificationLimitReachedError()

        templates = self._repository.list_pretesting_templates_for_season(
            season_id=testing_event.season_id,
        )

        allowed_score_codes, required_score_codes = (
            self._resolve_allowed_and_required_score_codes(
                templates=templates,
                bet_context_exceptions=bet_context.exceptions,
                session=session,
            )
        )

        answers_by_code = {
            answer.bet_score_code: answer
            for answer in answers
        }

        existing_answers_by_code = {}
        if current_bet is not None:
            existing_answers_by_code = {
                pick.bet_score_code: pick
                for pick in current_bet.picks
            }

        received_codes = set(answers_by_code)
        existing_codes = set(existing_answers_by_code)
        final_answer_codes = received_codes | existing_codes

        if not received_codes.issubset(allowed_score_codes):
            raise BetAnswerQuestionNotFoundError()

        if not required_score_codes.issubset(final_answer_codes):
            raise BetRequiredAnswerMissingError()

        score_ids_by_code = self._repository.get_bet_score_ids_by_codes(
            codes=received_codes,
        )
        if set(score_ids_by_code) != received_codes:
            raise BetAnswerQuestionNotFoundError()

        _validate_answer_relations(
            repository=self._repository,
            allowed_score_codes=allowed_score_codes,
            existing_answers=current_bet.picks if current_bet is not None else (),
            received_answers=answers,
        )

        resolved_powerups = BetPowerUpSubmissionValidator(self._repository).resolve(
            group_id=group_id,
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=None,
            testing_event_session_id=session.id if session is not None else None,
            powerups=powerups,
        )

        self._repository.upsert_user_bet_submission(
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=None,
            testing_event_session_id=session.id if session is not None else None,
            answers=answers,
            submitted_at=now,
        )

        if resolved_powerups:
            self._repository.create_powerup_uses_for_submission(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context.id,
                event_session_id=None,
                testing_event_session_id=session.id if session is not None else None,
                powerups=resolved_powerups,
            )

        if session is not None:
            return GetTestingEventSessionBetAnswers(self._repository).execute(
                testing_event_public_id=testing_event_public_id,
                testing_event_session_public_id=testing_event_session_public_id,
                group_id=group_id,
                user_id=user_id,
            )

        return GetTestingEventBetAnswers(self._repository).execute(
            testing_event_public_id=testing_event_public_id,
            group_id=group_id,
            user_id=user_id,
        )

    def _normal_window_is_open(
        self,
        *,
        now: datetime,
        betting_open_at: datetime | None,
        lock_cutoff: datetime | None,
    ) -> bool:
        if betting_open_at is not None and now < betting_open_at:
            return False
        if lock_cutoff is not None and now >= lock_cutoff:
            return False
        return True

    def _find_matching_edit_permission(
        self,
        *,
        permissions: list[BetEditPermissionDefinition],
        group_id: int,
        user_id: int,
        team_ids: set[int],
    ) -> BetEditPermissionDefinition | None:
        for permission in permissions:
            if permission.applies_to_all:
                return permission
            if permission.group_id == group_id:
                return permission
            if permission.user_id == user_id:
                return permission
            if permission.team_id is not None and permission.team_id in team_ids:
                return permission

        return None

    def _resolve_betting_window(
        self,
        *,
        testing_event: BetTestingEvent,
        session: BetTestingEventSession | None,
    ) -> tuple[datetime | None, datetime | None]:
        if session is not None:
            betting_open_at = session.betting_open_at
            lock_cutoff = session.lock_cutoff or session.scheduled_lock_cutoff
            return betting_open_at, lock_cutoff

        betting_open_at = testing_event.betting_open_at
        lock_cutoff = (
            testing_event.lock_cutoff
            or testing_event.scheduled_lock_cutoff
            or testing_event.event_start
            or testing_event.scheduled_event_start
        )
        return betting_open_at, lock_cutoff

    def _resolve_allowed_and_required_score_codes(
        self,
        *,
        templates: list[BetTemplateDefinition],
        bet_context_exceptions: tuple[BetExceptionDefinition, ...],
        session: BetTestingEventSession | None,
    ) -> tuple[set[str], set[str]]:
        allowed_codes: set[str] = set()
        required_codes: set[str] = set()
        score_id_by_code: dict[str, int] = {}

        for template in templates:
            if template.scope != BetTemplateScope.EVENT:
                continue

            for item in template.items:
                allowed_codes.add(item.bet_score.code)
                score_id_by_code[item.bet_score.code] = item.bet_score.id

                if item.required is True:
                    required_codes.add(item.bet_score.code)

        disabled_score_ids = {
            exception.bet_score_id
            for exception in bet_context_exceptions
            if exception.event_session_id is None
            and exception.is_disabled is True
        }

        return (
            {
                code
                for code in allowed_codes
                if score_id_by_code[code] not in disabled_score_ids
            },
            {
                code
                for code in required_codes
                if score_id_by_code[code] not in disabled_score_ids
            },
        )


class SubmitSeasonBetAnswers:
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def execute(
        self,
        *,
        season_year: int,
        group_id: int,
        user_id: int,
        team_ids: set[int],
        answers: list[BetAnswerInput],
        powerups: list[BetPowerUpUseInput],
    ) -> SeasonBetAnswersResult:
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForBetAnswersError()


        bet_context = self._repository.get_season_bet_context(
            group_id=group_id,
            season_id=season.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForSeasonError()

        now = datetime.now(timezone.utc)

        existing_bets = self._repository.list_user_bets_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        )

        if powerups and self._repository.user_has_any_submitted_bet_for_context(
            user_id=user_id,
            bet_context_id=bet_context.id,
        ):
            raise BetPowerUpsCannotBeUsedAfterSubmitError()

        current_bet = next(
            (
                bet
                for bet in existing_bets
                if bet.event_session_id is None
                and bet.testing_event_session_id is None
            ),
            None,
        )

        if current_bet is not None and current_bet.locked_at is not None:
            raise BetAnswersClosedError()

        is_modification = current_bet is not None and current_bet.submitted_at is not None

        betting_open_at, lock_cutoff = self._resolve_betting_window(
            season=season,
        )

        has_normal_window = self._normal_window_is_open(
            now=now,
            betting_open_at=betting_open_at,
            lock_cutoff=lock_cutoff,
        )

        matching_permission = None
        if not has_normal_window and is_modification:
            matching_permission = self._find_matching_edit_permission(
                permissions=self._repository.list_active_edit_permissions_for_scope(
                    bet_context_id=bet_context.id,
                    event_session_id=None,
                    testing_event_session_id=None,
                    now=now,
                ),
                group_id=group_id,
                user_id=user_id,
                team_ids=team_ids,
            )

        if not has_normal_window and matching_permission is None:
            if betting_open_at is not None and now < betting_open_at:
                raise BetAnswersNotOpenError()
            raise BetAnswersClosedError()

        max_modifications = (
            matching_permission.max_modifications
            if matching_permission is not None
            else None
        )
        if is_modification and max_modifications is not None:
            modification_count = max(current_bet.revision_count - 1, 0)
            if modification_count >= max_modifications:
                raise BetModificationLimitReachedError()

        templates = self._repository.list_season_templates_for_season(
            season_id=season.id,
        )

        allowed_score_codes, required_score_codes = (
            self._resolve_allowed_and_required_score_codes(
                templates=templates,
                bet_context_exceptions=bet_context.exceptions,
            )
        )

        answers_by_code = {
            answer.bet_score_code: answer
            for answer in answers
        }

        existing_answers_by_code = {}
        if current_bet is not None:
            existing_answers_by_code = {
                pick.bet_score_code: pick
                for pick in current_bet.picks
            }

        received_codes = set(answers_by_code)
        existing_codes = set(existing_answers_by_code)
        final_answer_codes = received_codes | existing_codes

        if not received_codes.issubset(allowed_score_codes):
            raise BetAnswerQuestionNotFoundError()

        if not required_score_codes.issubset(final_answer_codes):
            raise BetRequiredAnswerMissingError()

        score_ids_by_code = self._repository.get_bet_score_ids_by_codes(
            codes=received_codes,
        )
        if set(score_ids_by_code) != received_codes:
            raise BetAnswerQuestionNotFoundError()

        _validate_answer_relations(
            repository=self._repository,
            allowed_score_codes=allowed_score_codes,
            existing_answers=current_bet.picks if current_bet is not None else (),
            received_answers=answers,
        )

        resolved_powerups = BetPowerUpSubmissionValidator(self._repository).resolve(
            group_id=group_id,
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=None,
            testing_event_session_id=None,
            powerups=powerups,
        )

        self._repository.upsert_user_bet_submission(
            user_id=user_id,
            bet_context_id=bet_context.id,
            event_session_id=None,
            testing_event_session_id=None,
            answers=answers,
            submitted_at=now,
        )

        if resolved_powerups:
            self._repository.create_powerup_uses_for_submission(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context.id,
                event_session_id=None,
                testing_event_session_id=None,
                powerups=resolved_powerups,
            )

        return GetSeasonBetAnswers(self._repository).execute(
            season_year=season_year,
            group_id=group_id,
            user_id=user_id,
        )

    def _normal_window_is_open(
        self,
        *,
        now: datetime,
        betting_open_at: datetime | None,
        lock_cutoff: datetime | None,
    ) -> bool:
        if betting_open_at is not None and now < betting_open_at:
            return False
        if lock_cutoff is not None and now >= lock_cutoff:
            return False
        return True

    def _find_matching_edit_permission(
        self,
        *,
        permissions: list[BetEditPermissionDefinition],
        group_id: int,
        user_id: int,
        team_ids: set[int],
    ) -> BetEditPermissionDefinition | None:
        for permission in permissions:
            if permission.applies_to_all:
                return permission
            if permission.group_id == group_id:
                return permission
            if permission.user_id == user_id:
                return permission
            if permission.team_id is not None and permission.team_id in team_ids:
                return permission

        return None

    def _resolve_betting_window(
        self,
        *,
        season: BetSeason,
    ) -> tuple[datetime | None, datetime | None]:
        betting_open_at = season.betting_open_at
        lock_cutoff = season.lock_cutoff or season.scheduled_lock_cutoff
        return betting_open_at, lock_cutoff

    def _resolve_allowed_and_required_score_codes(
        self,
        *,
        templates: list[BetTemplateDefinition],
        bet_context_exceptions: tuple[BetExceptionDefinition, ...],
    ) -> tuple[set[str], set[str]]:
        allowed_codes: set[str] = set()
        required_codes: set[str] = set()
        score_id_by_code: dict[str, int] = {}

        for template in templates:
            if template.scope != BetTemplateScope.EVENT:
                continue

            for item in template.items:
                allowed_codes.add(item.bet_score.code)
                score_id_by_code[item.bet_score.code] = item.bet_score.id

                if item.required is True:
                    required_codes.add(item.bet_score.code)

        disabled_score_ids = {
            exception.bet_score_id
            for exception in bet_context_exceptions
            if exception.event_session_id is None
            and exception.is_disabled is True
        }

        return (
            {
                code
                for code in allowed_codes
                if score_id_by_code[code] not in disabled_score_ids
            },
            {
                code
                for code in required_codes
                if score_id_by_code[code] not in disabled_score_ids
            },
        )


class BetPowerUpSubmissionValidator:
    def __init__(self, repository: BetAnswersRepository):
        self._repository = repository

    def resolve(
        self,
        *,
        group_id: int,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        powerups: list[BetPowerUpUseInput],
    ) -> list[ResolvedBetPowerUpUse]:
        resolved: list[ResolvedBetPowerUpUse] = []

        for requested in powerups:
            assignment = self._repository.get_powerup_assignment_for_submission(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context_id,
                powerup_code=requested.powerup_code,
            )

            if assignment is None:
                raise BetPowerUpNotAssignedError()

            if not assignment.is_enabled:
                raise BetPowerUpDisabledError()

            if assignment.quantity <= 0:
                raise BetPowerUpNotAssignedError()

            if self._repository.powerup_already_used(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context_id,
                powerup_id=assignment.powerup_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
            ):
                raise BetPowerUpAlreadyUsedError()

            if self._repository.powerup_is_restricted(
                powerup_id=assignment.powerup_id,
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
            ):
                raise BetPowerUpRestrictedError()

            targets = self._resolve_targets(
                group_id=group_id,
                actor_user_id=user_id,
                bet_context_id=bet_context_id,
                assignment=assignment,
                requested_targets=requested.targets,
            )

            resolved.append(
                ResolvedBetPowerUpUse(
                    powerup_id=assignment.powerup_id,
                    rule_json=requested.rule_json,
                    targets=targets,
                )
            )

        return resolved

    def _resolve_targets(
        self,
        *,
        group_id: int,
        actor_user_id: int,
        bet_context_id: int,
        assignment: BetPowerUpAssignmentDefinition,
        requested_targets: list[BetPowerUpTargetInput],
    ) -> list[ResolvedBetPowerUpTarget]:
        if assignment.code.startswith("HALVE_POINTS") and not requested_targets:
            raise BetPowerUpTargetRequiredError()

        if assignment.target_mode == "SINGLE" and len(requested_targets) > 1:
            raise BetPowerUpTargetNotAllowedError()

        if assignment.code.startswith("DOUBLE_POINTS") and requested_targets:
            raise BetPowerUpTargetNotAllowedError()

        resolved: list[ResolvedBetPowerUpTarget] = []

        for target in requested_targets:
            if assignment.code.startswith("HALVE_POINTS"):
                if target.target_type != "USER":
                    raise BetPowerUpTargetNotAllowedError()

                if target.target_user_public_id is None:
                    raise BetPowerUpTargetNotAllowedError()

                target_user_id = self._repository.get_user_id_by_public_id(
                    target.target_user_public_id,
                )

                if target_user_id is None or target_user_id == actor_user_id:
                    raise BetPowerUpTargetNotAllowedError()

                received_contexts = self._repository.count_distinct_contexts_where_user_received_powerup(
                    group_id=group_id,
                    target_user_id=target_user_id,
                    powerup_id=assignment.powerup_id,
                    excluding_bet_context_id=bet_context_id,
                )

                if received_contexts >= 2:
                    raise BetPowerUpPenaltyLimitReachedError()

                resolved.append(
                    ResolvedBetPowerUpTarget(
                        target_type=target.target_type,
                        target_user_id=target_user_id,
                        rule_json=target.rule_json,
                    )
                )
                continue

            raise BetPowerUpTargetNotAllowedError()

        return resolved
