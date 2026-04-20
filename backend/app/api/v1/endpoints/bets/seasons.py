from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyBetQuestionsRepository
from app.api.deps import require_group_member, _translate_bets_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group

from app.domain.bets import BetsError
from app.domain.bets.use_cases import (
    GetSeasonBetQuestions,
    GetSeasonBetAnswers,
)
from app.models.bets import (
    BetAnswerRead,
    BetQuestionRead,
    BetQuestionOptionRead,
    SeasonBetQuestionsResponse,
    SeasonBetAnswersResponse,
)

router = APIRouter()

@router.get(
    "/seasons/{season_year}/questions",
    response_model=SeasonBetQuestionsResponse,
    response_model_exclude_none=True,
)
def get_season_questions(
    season_year: int,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> SeasonBetQuestionsResponse:
    _, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetQuestionsRepository(db)
    use_case = GetSeasonBetQuestions(repository)

    try:
        result = use_case.execute(
            season_year=season_year,
            group_id=group.id,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return SeasonBetQuestionsResponse(
        bet_context_public_id=result.bet_context_public_id,
        kind=result.kind,
        season_year=result.season_year,
        label=result.label,
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
            for question in result.questions
        ],
    )


@router.get(
    "/seasons/{season_year}/answers",
    response_model=SeasonBetAnswersResponse,
    response_model_exclude_none=True,
)
def get_season_answers(
    season_year: int,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> SeasonBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetQuestionsRepository(db)
    use_case = GetSeasonBetAnswers(repository)

    try:
        result = use_case.execute(
            season_year=season_year,
            group_id=group.id,
            user_id=user.id,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return SeasonBetAnswersResponse(
        bet_context_public_id=result.bet_context_public_id,
        kind=result.kind,
        season_year=result.season_year,
        label=result.label,
        submitted_at=result.submitted_at,
        last_modified_at=result.last_modified_at,
        locked_at=result.locked_at,
        answers=[
            BetAnswerRead(
                bet_score_code=answer.bet_score_code,
                value=answer.value,
            )
            for answer in result.answers
        ],
    )