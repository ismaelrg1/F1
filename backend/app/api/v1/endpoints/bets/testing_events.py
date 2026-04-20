from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyBetQuestionsRepository
from app.api.deps import require_group_member, _translate_bets_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group

from app.domain.bets import BetsError
from app.domain.bets.answers.models import BetAnswerInput
from app.domain.bets.use_cases import (
    GetTestingEventBetQuestions,
    GetTestingEventBetAnswers,
    GetTestingEventSessionBetAnswers,
    PatchTestingEventBetAnswers,
)
from app.models.bets import (
    BetAnswerRead,
    BetAnswersPatchRequest,
    BetQuestionRead,
    BetQuestionOptionRead,
    TestingEventBetQuestionsResponse,
    TestingEventBetQuestionsSessionRead,
    TestingEventBetAnswersResponse,
    TestingEventBetAnswersSessionResponse,
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
        bet_context_public_id=result.bet_context_public_id,
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

    repository = SqlAlchemyBetQuestionsRepository(db)

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
        bet_context_public_id=result.bet_context_public_id,
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

    repository = SqlAlchemyBetQuestionsRepository(db)
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
        bet_context_public_id=result.bet_context_public_id,
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
