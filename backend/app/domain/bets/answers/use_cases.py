from uuid import UUID

from app.domain.bets.shared.ports import BetQuestionsRepository
from app.domain.bets.answers.models import (
    RaceEventBetAnswersResult,
    RaceEventBetAnswersSessionResult,
    TestingEventBetAnswersResult,
    TestingEventBetAnswersSessionResult,
)
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    BetContextNotFoundForTestingEventError,
    RaceEventNotFoundForBetQuestionsError,
    RaceEventSessionNotFoundForBetAnswersError,
    TestingEventNotFoundForBetQuestionsError,
    TestingEventSessionNotFoundForBetAnswersError,
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
