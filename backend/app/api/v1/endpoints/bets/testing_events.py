from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyBetAnswersRepository, SqlAlchemyBetQuestionsRepository, SqlAlchemyBetResultsRepository, SqlAlchemyBetPowerUpsRepository
from app.api.deps import require_group_member, _translate_bets_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group

from app.domain.bets import BetsError
from app.domain.bets.models import BetAnswerInput
from app.domain.bets.answers.models import BetPowerUpTargetInput, BetPowerUpUseInput
from app.domain.bets.powerups import GetTestingEventPowerUps
from app.domain.bets.use_cases import (
    GetTestingEventBetQuestions,
    GetTestingEventBetAnswers,
    GetTestingEventSessionBetAnswers,
    GetTestingEventSessionBetResults,
    PatchTestingEventBetAnswers,
    SubmitTestingEventBetAnswers,
)
from app.models.bets import (
    BetAnswerRead,
    BetAnswersPatchRequest,
    BetAnswersSubmitRequest,
    BetQuestionRead,
    BetQuestionOptionRead,
    TestingEventBetQuestionsResponse,
    TestingEventBetQuestionsSessionRead,
    TestingEventBetAnswersResponse,
    TestingEventBetAnswersSessionResponse,
    BetPowerUpRead,
    TestingEventBetPowerUpsResponse,
    BetPowerUpTargetOptionRead,
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
    TestingEventSessionBetResultsResponse,
)

router = APIRouter()

@router.get(
    "/testing-events/{testing_event_public_id}/questions",
    response_model=TestingEventBetQuestionsResponse,
    response_model_exclude_none=True,
)
def get_testing_event_questions(
    testing_event_public_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> TestingEventBetQuestionsResponse:
    _, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)


    repository = SqlAlchemyBetQuestionsRepository(db)
    use_case = GetTestingEventBetQuestions(repository)

    try:
        result = use_case.execute(
            testing_event_public_id=testing_event_public_id,
            group_id=group.id,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return TestingEventBetQuestionsResponse(
        kind=result.kind,
        testing_event_public_id=result.testing_event_public_id,
        label=result.label,
        status=result.status,
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
            TestingEventBetQuestionsSessionRead(
                testing_event_session_public_id=session.testing_event_session_public_id,
                session_order=session.session_order,
                name=session.name,
                start_datetime=session.start_datetime,
                end_datetime=session.end_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                scheduled_end_datetime=session.scheduled_end_datetime,
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
    "/testing-events/{testing_event_public_id}/answers",
    response_model=TestingEventBetAnswersResponse,
    response_model_exclude_none=True,
)
def get_testing_event_answers(
    testing_event_public_id: UUID,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> TestingEventBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetAnswersRepository(db)

    try:
        if session_id is not None:
            use_case = GetTestingEventSessionBetAnswers(repository)
            result = use_case.execute(
                testing_event_public_id=testing_event_public_id,
                testing_event_session_public_id=session_id,
                group_id=group.id,
                user_id=user.id,
            )
        else:
            use_case = GetTestingEventBetAnswers(repository)
            result = use_case.execute(
                testing_event_public_id=testing_event_public_id,
                group_id=group.id,
                user_id=user.id,
            )

    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return TestingEventBetAnswersResponse(
        kind=result.kind,
        testing_event_public_id=result.testing_event_public_id,
        label=result.label,
        status=result.status,
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
            TestingEventBetAnswersSessionResponse(
                testing_event_session_public_id=session.testing_event_session_public_id,
                session_order=session.session_order,
                name=session.name,
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
    "/testing-events/{testing_event_public_id}/answers",
    response_model=TestingEventBetAnswersResponse,
    response_model_exclude_none=True,
)
def patch_testing_event_answers(
    testing_event_public_id: UUID,
    payload: BetAnswersPatchRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> TestingEventBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetAnswersRepository(db)
    use_case = PatchTestingEventBetAnswers(repository)

    try:
        result = use_case.execute(
            testing_event_public_id=testing_event_public_id,
            testing_event_session_public_id=session_id,
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

    return TestingEventBetAnswersResponse(
        kind=result.kind,
        testing_event_public_id=result.testing_event_public_id,
        label=result.label,
        status=result.status,
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
            TestingEventBetAnswersSessionResponse(
                testing_event_session_public_id=session.testing_event_session_public_id,
                session_order=session.session_order,
                name=session.name,
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
    "/testing-events/{testing_event_public_id}/answers",
    response_model=TestingEventBetAnswersResponse,
    response_model_exclude_none=True,
)
def submit_testing_event_answers(
    testing_event_public_id: UUID,
    payload: BetAnswersSubmitRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> TestingEventBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetAnswersRepository(db)
    use_case = SubmitTestingEventBetAnswers(repository)

    try:
        result = use_case.execute(
            testing_event_public_id=testing_event_public_id,
            testing_event_session_public_id=session_id,
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
            powerups=[
                BetPowerUpUseInput(
                    powerup_code=powerup.powerup_code,
                    targets=[
                        BetPowerUpTargetInput(
                            target_type=target.target_type,
                            target_user_public_id=target.target_user_public_id,
                            target_team_public_id=target.target_team_public_id,
                            target_group_public_id=target.target_group_public_id,
                            rule_json=target.rule_json,
                        )
                        for target in powerup.targets
                    ],
                    rule_json=powerup.rule_json,
                )
                for powerup in payload.powerups
            ],
        )
        db.commit()
    except BetsError as exc:
        db.rollback()
        raise _translate_bets_error(exc, locale=locale) from exc

    return TestingEventBetAnswersResponse(
        kind=result.kind,
        testing_event_public_id=result.testing_event_public_id,
        label=result.label,
        status=result.status,
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
            TestingEventBetAnswersSessionResponse(
                testing_event_session_public_id=session.testing_event_session_public_id,
                session_order=session.session_order,
                name=session.name,
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
    "/testing-events/{testing_event_public_id}/results",
    response_model=TestingEventSessionBetResultsResponse,
    response_model_exclude_none=True,
)
def get_testing_event_results(
    testing_event_public_id: UUID,
    request: Request,
    session_id: UUID = Query(...),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> TestingEventSessionBetResultsResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetResultsRepository(db)
    use_case = GetTestingEventSessionBetResults(repository)

    try:
        result = use_case.execute(
            testing_event_public_id=testing_event_public_id,
            testing_event_session_public_id=session_id,
            group_id=group.id,
            user_id=user.id,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return TestingEventSessionBetResultsResponse(
        kind=result.kind,
        testing_event_public_id=result.testing_event_public_id,
        label=result.label,
        scope=BetResultsScopeRead(
            type=result.scope.type,
            testing_event_public_id=result.scope.testing_event_public_id,
            testing_event_session_public_id=result.scope.testing_event_session_public_id,
            session_order=result.scope.session_order,
            name=result.scope.name,
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

@router.get(
    "/testing-events/{testing_event_public_id}/powerups",
    response_model=TestingEventBetPowerUpsResponse,
)
def get_testing_event_powerups(
    testing_event_public_id: UUID,
    request: Request,
    session_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> TestingEventBetPowerUpsResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetPowerUpsRepository(db)
    use_case = GetTestingEventPowerUps(repository)

    try:
        result = use_case.execute(
            group_id=group.id,
            user_id=user.id,
            testing_event_public_id=testing_event_public_id,
            testing_event_session_public_id=session_id,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return TestingEventBetPowerUpsResponse(
        testing_event_public_id=result.testing_event_public_id,
        powerups=[
            BetPowerUpRead(
                code=powerup.code,
                name=powerup.name,
                target_mode=powerup.target_mode,
                quantity=powerup.quantity,
                is_enabled=powerup.is_enabled,
                is_restricted=powerup.is_restricted,
                already_used=powerup.already_used,
                target_options=[
                    BetPowerUpTargetOptionRead(
                        target_type=target.target_type,
                        target_user_public_id=target.target_user_public_id,
                        target_team_public_id=target.target_team_public_id,
                        target_group_public_id=target.target_group_public_id,
                        label=target.label,
                        is_available=target.is_available,
                        unavailable_reason=target.unavailable_reason,
                    )
                    for target in powerup.target_options
                ],
            )
            for powerup in result.powerups
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
