from uuid import UUID

from app.domain.bets.models import BetQuestionResult
from app.domain.bets.ports import BetQuestionsRepository
from app.domain.bets.use_cases import (
    GetRaceEventBetQuestions,
    GetSeasonBetQuestions,
    GetTestingEventBetQuestions,
)
from app.domain.management.official_results.answers.ports import OfficialResultAnswersRepository
from app.domain.management.official_results.questions.models import (
    ExistingOfficialResult,
    OfficialResultQuestion,
    OfficialResultScopeKey,
    OfficialResultScopeStatus,
    RaceEventOfficialResultsForm,
    RaceEventOfficialResultsSession,
    SeasonOfficialResultsForm,
    TestingEventOfficialResultsForm,
    TestingEventOfficialResultsSession,
)
from app.domain.management.official_results.questions.ports import OfficialResultQuestionsRepository


class GetRaceEventOfficialResultsForm:
    def __init__(
        self,
        bet_questions_repository: BetQuestionsRepository,
        official_results_repository: OfficialResultQuestionsRepository | OfficialResultAnswersRepository,
    ):
        self._bet_questions_repository = bet_questions_repository
        self._official_results_repository = official_results_repository

    def execute(self, *, race_event_public_id: UUID, group_id: int) -> RaceEventOfficialResultsForm:
        bet_form = GetRaceEventBetQuestions(self._bet_questions_repository).execute(
            race_event_public_id=race_event_public_id,
            group_id=group_id,
        )

        bet_context_id, _ = self._official_results_repository.get_bet_context_scope(
            bet_context_public_id=bet_form.bet_context_public_id,
        )

        existing = _index_existing(
            self._official_results_repository.list_official_results_for_context(
                bet_context_id=bet_context_id,
            )
        )
        published = self._official_results_repository.list_result_publications_for_context(
            bet_context_id=bet_context_id,
        )

        event_scope = OfficialResultScopeKey(
            event_session_public_id=None,
            testing_event_session_public_id=None,
        )

        return RaceEventOfficialResultsForm(
            kind=bet_form.kind,
            race_event_public_id=bet_form.race_event_public_id,
            label=bet_form.label,
            scope_status=_scope_status(event_scope, existing, published),
            event_questions=_merge_questions(bet_form.event_questions, existing.get(event_scope, {})),
            sessions=[
                RaceEventOfficialResultsSession(
                    event_session_public_id=session.event_session_public_id,
                    session_type=session.session_type,
                    start_datetime=session.start_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    lock_cutoff=session.lock_cutoff,
                    scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                    status=session.status,
                    scope_status=_scope_status(
                        OfficialResultScopeKey(session.event_session_public_id, None),
                        existing,
                        published,
                    ),
                    questions=_merge_questions(
                        session.questions,
                        existing.get(OfficialResultScopeKey(session.event_session_public_id, None), {}),
                    ),
                )
                for session in bet_form.sessions
            ],
        )


class GetTestingEventOfficialResultsForm:
    def __init__(
        self,
        bet_questions_repository: BetQuestionsRepository,
        official_results_repository: OfficialResultQuestionsRepository | OfficialResultAnswersRepository,
    ):
        self._bet_questions_repository = bet_questions_repository
        self._official_results_repository = official_results_repository

    def execute(self, *, testing_event_public_id: UUID, group_id: int) -> TestingEventOfficialResultsForm:
        bet_form = GetTestingEventBetQuestions(self._bet_questions_repository).execute(
            testing_event_public_id=testing_event_public_id,
            group_id=group_id,
        )

        bet_context_id, _ = self._official_results_repository.get_bet_context_scope(
            bet_context_public_id=bet_form.bet_context_public_id,
        )

        existing = _index_existing(
            self._official_results_repository.list_official_results_for_context(
                bet_context_id=bet_context_id,
            )
        )
        published = self._official_results_repository.list_result_publications_for_context(
            bet_context_id=bet_context_id,
        )

        event_scope = OfficialResultScopeKey(None, None)

        return TestingEventOfficialResultsForm(
            kind=bet_form.kind,
            testing_event_public_id=bet_form.testing_event_public_id,
            label=bet_form.label,
            status=bet_form.status,
            scope_status=_scope_status(event_scope, existing, published),
            event_questions=_merge_questions(bet_form.event_questions, existing.get(event_scope, {})),
            sessions=[
                TestingEventOfficialResultsSession(
                    testing_event_session_public_id=session.testing_event_session_public_id,
                    session_order=session.session_order,
                    name=session.name,
                    start_datetime=session.start_datetime,
                    end_datetime=session.end_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    scheduled_end_datetime=session.scheduled_end_datetime,
                    scope_status=_scope_status(
                        OfficialResultScopeKey(None, session.testing_event_session_public_id),
                        existing,
                        published,
                    ),
                    questions=_merge_questions(
                        session.questions,
                        existing.get(OfficialResultScopeKey(None, session.testing_event_session_public_id), {}),
                    ),
                )
                for session in bet_form.sessions
            ],
        )


class GetSeasonOfficialResultsForm:
    def __init__(
        self,
        bet_questions_repository: BetQuestionsRepository,
        official_results_repository: OfficialResultQuestionsRepository | OfficialResultAnswersRepository,
    ):
        self._bet_questions_repository = bet_questions_repository
        self._official_results_repository = official_results_repository

    def execute(self, *, season_year: int, group_id: int) -> SeasonOfficialResultsForm:
        bet_form = GetSeasonBetQuestions(self._bet_questions_repository).execute(
            season_year=season_year,
            group_id=group_id,
        )

        bet_context_id, _ = self._official_results_repository.get_bet_context_scope(
            bet_context_public_id=bet_form.bet_context_public_id,
        )

        existing = _index_existing(
            self._official_results_repository.list_official_results_for_context(
                bet_context_id=bet_context_id,
            )
        )
        published = self._official_results_repository.list_result_publications_for_context(
            bet_context_id=bet_context_id,
        )

        scope = OfficialResultScopeKey(None, None)

        return SeasonOfficialResultsForm(
            kind=bet_form.kind,
            season_year=bet_form.season_year,
            label=bet_form.label,
            scope_status=_scope_status(scope, existing, published),
            questions=_merge_questions(bet_form.questions, existing.get(scope, {})),
        )


def _index_existing(
    results: list[ExistingOfficialResult],
) -> dict[OfficialResultScopeKey, dict[str, ExistingOfficialResult]]:
    indexed: dict[OfficialResultScopeKey, dict[str, ExistingOfficialResult]] = {}

    for result in results:
        scope = OfficialResultScopeKey(
            event_session_public_id=result.event_session_public_id,
            testing_event_session_public_id=result.testing_event_session_public_id,
        )
        indexed.setdefault(scope, {})[result.bet_score_code] = result

    return indexed


def _scope_status(
    scope: OfficialResultScopeKey,
    existing: dict[OfficialResultScopeKey, dict[str, ExistingOfficialResult]],
    published: set[OfficialResultScopeKey],
) -> OfficialResultScopeStatus:
    has_results = bool(existing.get(scope))

    return OfficialResultScopeStatus(
        has_official_results=has_results,
        results_published=scope in published,
        write_method="PATCH" if has_results else "POST",
    )


def _merge_questions(
    questions: list[BetQuestionResult],
    existing_by_code: dict[str, ExistingOfficialResult],
) -> list[OfficialResultQuestion]:
    return [
        OfficialResultQuestion(
            code=question.code,
            label=question.label,
            value_type=question.value_type,
            required=question.required,
            display_order=question.display_order,
            base_points=question.base_points,
            constraints_json=question.constraints_json,
            options=question.options,
            official_value=existing_by_code[question.code].value if question.code in existing_by_code else None,
            official_source=existing_by_code[question.code].source if question.code in existing_by_code else None,
            official_created_at=existing_by_code[question.code].created_at if question.code in existing_by_code else None,
        )
        for question in questions
    ]