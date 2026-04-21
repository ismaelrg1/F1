from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyBetQuestionsRepository, SqlAlchemyBetResultsRepository
from app.api.deps import require_group_member, _translate_bets_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group

from app.domain.bets import BetsError
from app.domain.bets.models import BetAnswerInput
from app.domain.bets.use_cases import (
    # Answers
    GetRaceEventBetAnswers,
    GetRaceEventSessionBetAnswers,
    PatchRaceEventBetAnswers,
    SubmitRaceEventBetAnswers,

    # Questions
    GetRaceEventBetQuestions,

    # Results
    GetRaceEventBetResults,
    GetRaceEventSessionBetResults
)
from app.models.bets import (
    BetAnswerRead,
    BetAnswersPatchRequest,
    BetQuestionRead,
    BetQuestionOptionRead,
    RaceEventBetAnswersResponse,
    RaceEventBetAnswersSessionResponse,
    RaceEventBetQuestionsResponse,
    RaceEventBetQuestionsSessionRead,
)
from app.models.bet_results import (
    BetOfficialResultRead,
    BetResultAnswerRead,
    BetResultEntryRead,
    BetResultScoreRead,
    BetResultsComponentRead,
    BetResultsPointsRead,
    BetResultsScopeRead,
    BetResultsUserRead,
    BetResultsVisibilityRead,
    RaceEventBetResultsBlockRead,
    RaceEventBetResultsResponse,
    RaceEventBetResultsSessionRead,
    RaceEventSessionBetResultsResponse,
)

router = APIRouter()


@router.get(
    "/race-events/{race_event_public_id}/questions",
    response_model=RaceEventBetQuestionsResponse,
    response_model_exclude_none=True,
)
def get_race_event_questions(
    race_event_public_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> RaceEventBetQuestionsResponse:
    _, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetQuestionsRepository(db)
    use_case = GetRaceEventBetQuestions(repository)

    try:
        result = use_case.execute(
            race_event_public_id=race_event_public_id,
            group_id=group.id,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return RaceEventBetQuestionsResponse(
        bet_context_public_id=result.bet_context_public_id,
        kind=result.kind,
        race_event_public_id=result.race_event_public_id,
        label=result.label,
        event_questions=[
            BetQuestionRead(
                code=question.code,
                label=question.label,
                value_type=question.value_type,
                required=question.required,
                display_order=question.display_order,
                base_points=question.base_points,
                constraints_json=question.constraints_json,
                options=(
                    [
                        BetQuestionOptionRead(value=option.value, label=option.label)
                        if option.meta is None
                        else BetQuestionOptionRead(value=option.value, label=option.label, meta=option.meta)
                        for option in question.options
                    ]
                    if question.options is not None
                    else None
                ),
            )
            for question in result.event_questions
        ],
        sessions=[
            RaceEventBetQuestionsSessionRead(
                event_session_public_id=session.event_session_public_id,
                session_type=session.session_type,
                start_datetime=session.start_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                lock_cutoff=session.lock_cutoff,
                scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                status=session.status,
                questions=[
                    BetQuestionRead(
                        code=question.code,
                        label=question.label,
                        value_type=question.value_type,
                        required=question.required,
                        display_order=question.display_order,
                        base_points=question.base_points,
                        constraints_json=question.constraints_json,
                        options=(
                            [
                                BetQuestionOptionRead(value=option.value, label=option.label)
                                if option.meta is None
                                else BetQuestionOptionRead(value=option.value, label=option.label, meta=option.meta)
                                for option in question.options
                            ]
                            if question.options is not None
                            else None
                        ),
                    )
                    for question in session.questions
                ],
            )
            for session in result.sessions
        ],
    )


@router.get(
    "/race-events/{race_event_public_id}/answers",
    response_model=RaceEventBetAnswersResponse ,
    response_model_exclude_none=True,
)
def get_race_event_answers(
    race_event_public_id: UUID,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> RaceEventBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetQuestionsRepository(db)

    try:
        if session_id is not None:
            use_case = GetRaceEventSessionBetAnswers(repository)
            result = use_case.execute(
                race_event_public_id=race_event_public_id,
                event_session_public_id=session_id,
                group_id=group.id,
                user_id=user.id,
            )

        else:
            use_case = GetRaceEventBetAnswers(repository)
            result = use_case.execute(
                race_event_public_id=race_event_public_id,
                group_id=group.id,
                user_id=user.id,
            )

    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return RaceEventBetAnswersResponse(
        bet_context_public_id=result.bet_context_public_id,
        kind=result.kind,
        race_event_public_id=result.race_event_public_id,
        label=result.label,
        submitted_at=result.submitted_at,
        last_modified_at=result.last_modified_at,
        locked_at=result.locked_at,
        event_answers=[
            BetAnswerRead(
                bet_score_code=answer.bet_score_code,
                value=answer.value,
            )
            for answer in result.event_answers
        ],
        sessions=[
            RaceEventBetAnswersSessionResponse(
                event_session_public_id=session.event_session_public_id,
                session_type=session.session_type,
                submitted_at=session.submitted_at,
                last_modified_at=session.last_modified_at,
                locked_at=session.locked_at,
                answers=[
                    BetAnswerRead(
                        bet_score_code=answer.bet_score_code,
                        value=answer.value,
                    )
                    for answer in session.answers
                ],
            )
            for session in result.sessions
        ],
    )


@router.patch(
    "/race-events/{race_event_public_id}/answers",
    response_model=RaceEventBetAnswersResponse,
    response_model_exclude_none=True,
)
def patch_race_event_answers(
    race_event_public_id: UUID,
    payload: BetAnswersPatchRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> RaceEventBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetQuestionsRepository(db)
    use_case = PatchRaceEventBetAnswers(repository)

    try:
        result = use_case.execute(
            race_event_public_id=race_event_public_id,
            event_session_public_id=session_id,
            group_id=group.id,
            user_id=user.id,
            answers=[
                BetAnswerInput(
                    bet_score_code=answer.bet_score_code,
                    value=answer.value,
                )
                for answer in payload.answers
            ],
        )
        db.commit()
    except BetsError as exc:
        db.rollback()
        raise _translate_bets_error(exc, locale=locale) from exc

    return RaceEventBetAnswersResponse(
        bet_context_public_id=result.bet_context_public_id,
        kind=result.kind,
        race_event_public_id=result.race_event_public_id,
        label=result.label,
        submitted_at=result.submitted_at,
        last_modified_at=result.last_modified_at,
        locked_at=result.locked_at,
        event_answers=[
            BetAnswerRead(
                bet_score_code=answer.bet_score_code,
                value=answer.value,
            )
            for answer in result.event_answers
        ],
        sessions=[
            RaceEventBetAnswersSessionResponse(
                event_session_public_id=session.event_session_public_id,
                session_type=session.session_type,
                submitted_at=session.submitted_at,
                last_modified_at=session.last_modified_at,
                locked_at=session.locked_at,
                answers=[
                    BetAnswerRead(
                        bet_score_code=answer.bet_score_code,
                        value=answer.value,
                    )
                    for answer in session.answers
                ],
            )
            for session in result.sessions
        ],
    )

@router.post(
    "/race-events/{race_event_public_id}/answers",
    response_model=RaceEventBetAnswersResponse,
    response_model_exclude_none=True,
)
def submit_race_event_answers(
    race_event_public_id: UUID,
    payload: BetAnswersPatchRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> RaceEventBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetQuestionsRepository(db)
    use_case = SubmitRaceEventBetAnswers(repository)

    try:
        result = use_case.execute(
            race_event_public_id=race_event_public_id,
            event_session_public_id=session_id,
            group_id=group.id,
            user_id=user.id,
            team_ids=set(),
            answers=[
                BetAnswerInput(
                    bet_score_code=answer.bet_score_code,
                    value=answer.value,
                )
                for answer in payload.answers
            ],
        )
        db.commit()
    except BetsError as exc:
        db.rollback()
        raise _translate_bets_error(exc, locale=locale) from exc

    return RaceEventBetAnswersResponse(
        bet_context_public_id=result.bet_context_public_id,
        kind=result.kind,
        race_event_public_id=result.race_event_public_id,
        label=result.label,
        submitted_at=result.submitted_at,
        last_modified_at=result.last_modified_at,
        locked_at=result.locked_at,
        event_answers=[
            BetAnswerRead(
                bet_score_code=answer.bet_score_code,
                value=answer.value,
            )
            for answer in result.event_answers
        ],
        sessions=[
            RaceEventBetAnswersSessionResponse(
                event_session_public_id=session.event_session_public_id,
                session_type=session.session_type,
                submitted_at=session.submitted_at,
                last_modified_at=session.last_modified_at,
                locked_at=session.locked_at,
                answers=[
                    BetAnswerRead(
                        bet_score_code=answer.bet_score_code,
                        value=answer.value,
                    )
                    for answer in session.answers
                ],
            )
            for session in result.sessions
        ],
    )

@router.get(
    "/race-events/{race_event_public_id}/results",
    response_model=RaceEventBetResultsResponse | RaceEventSessionBetResultsResponse,
    response_model_exclude_none=True,
)
def get_race_event_results(
    race_event_public_id: UUID,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> RaceEventBetResultsResponse | RaceEventSessionBetResultsResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetResultsRepository(db)

    try:
        if session_id is not None:
            use_case = GetRaceEventSessionBetResults(repository)
            result = use_case.execute(
                race_event_public_id=race_event_public_id,
                event_session_public_id=session_id,
                group_id=group.id,
                user_id=user.id,
            )

            return RaceEventSessionBetResultsResponse(
                bet_context_public_id=result.bet_context_public_id,
                kind=result.kind,
                race_event_public_id=result.race_event_public_id,
                label=result.label,
                scope=BetResultsScopeRead(
                    type=result.scope.type,
                    race_event_public_id=result.scope.race_event_public_id,
                    event_session_public_id=result.scope.event_session_public_id,
                    session_type=result.scope.session_type,
                ),
                visibility=_map_visibility(result.visibility),
                official_results=[
                    _map_official_result(official_result)
                    for official_result in result.official_results
                ],
                entries=[
                    _map_entry(entry)
                    for entry in result.entries
                ],
            )

        use_case = GetRaceEventBetResults(repository)
        result = use_case.execute(
            race_event_public_id=race_event_public_id,
            group_id=group.id,
            user_id=user.id,
        )

    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return RaceEventBetResultsResponse(
        bet_context_public_id=result.bet_context_public_id,
        kind=result.kind,
        race_event_public_id=result.race_event_public_id,
        label=result.label,
        event_results=RaceEventBetResultsBlockRead(
            scope=BetResultsScopeRead(
                type=result.event_results.scope.type,
                race_event_public_id=result.event_results.scope.race_event_public_id,
                event_session_public_id=result.event_results.scope.event_session_public_id,
                session_type=result.event_results.scope.session_type,
            ),
            visibility=_map_visibility(result.event_results.visibility),
            official_results=[
                _map_official_result(official_result)
                for official_result in result.event_results.official_results
            ],
            entries=[
                _map_entry(entry)
                for entry in result.event_results.entries
            ],
        ),
        sessions=[
            RaceEventBetResultsSessionRead(
                event_session_public_id=session.event_session_public_id,
                session_type=session.session_type,
                start_datetime=session.start_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                lock_cutoff=session.lock_cutoff,
                scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                status=session.status,
                visibility=_map_visibility(session.visibility),
                official_results=[
                    _map_official_result(official_result)
                    for official_result in session.official_results
                ],
                entries=[
                    _map_entry(entry)
                    for entry in session.entries
                ],
            )
            for session in result.sessions
        ],
    )


def _map_points(points) -> BetResultsPointsRead:
    return BetResultsPointsRead(
        base=points.base,
        powerup=points.powerup,
        extra=points.extra,
        penalty=points.penalty,
        total=points.total,
    )


def _map_component(component) -> BetResultsComponentRead:
    return BetResultsComponentRead(
        type=component.type,
        code=component.code,
        points=component.points,
        applies_to=component.applies_to,
        details=component.details,
    )


def _map_visibility(visibility) -> BetResultsVisibilityRead:
    return BetResultsVisibilityRead(
        mode=visibility.mode,
        can_view_group_results=visibility.can_view_group_results,
        reason=visibility.reason,
        is_locked=visibility.is_locked,
        results_published=visibility.results_published,
        results_published_at=visibility.results_published_at,
        viewer_submitted=visibility.viewer_submitted,
    )


def _map_official_result(result) -> BetOfficialResultRead:
    return BetOfficialResultRead(
        bet_score_code=result.bet_score_code,
        label=result.label,
        value=result.value,
        source=result.source,
        created_at=result.created_at,
    )


def _map_answer(answer) -> BetResultAnswerRead:
    return BetResultAnswerRead(
        bet_score_code=answer.bet_score_code,
        label=answer.label,
        value=answer.value,
        is_invalid=answer.is_invalid,
        invalid_reason=answer.invalid_reason,
        official_value=answer.official_value,
        is_correct=answer.is_correct,
        points=_map_points(answer.points),
        components=[_map_component(component) for component in answer.components],
    )


def _map_entry(entry) -> BetResultEntryRead:
    return BetResultEntryRead(
        user=BetResultsUserRead(
            public_id=entry.user.public_id,
            username=entry.user.username,
            display_name=entry.user.display_name,
        ),
        submitted_at=entry.submitted_at,
        last_modified_at=entry.last_modified_at,
        locked_at=entry.locked_at,
        answers=[_map_answer(answer) for answer in entry.answers],
        score=(
            BetResultScoreRead(
                points=_map_points(entry.score.points),
                components=[_map_component(component) for component in entry.score.components],
                computed_at=entry.score.computed_at,
            )
            if entry.score is not None
            else None
        ),
    )