from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyBetQuestionsRepository
from app.api.deps import require_group_member, _translate_bets_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group

from app.domain.bets import BetsError
from app.domain.bets.use_cases import (
    GetRaceEventBetAnswers,
    GetRaceEventBetQuestions,
    GetRaceEventSessionBetAnswers,
)
from app.models.bets import (
    BetAnswerRead,
    BetQuestionRead,
    BetQuestionOptionRead,
    RaceEventBetAnswersResponse,
    RaceEventBetAnswersSessionResponse,
    RaceEventBetQuestionsResponse,
    RaceEventBetQuestionsSessionRead,
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