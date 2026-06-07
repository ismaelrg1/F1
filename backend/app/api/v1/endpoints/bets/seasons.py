from fastapi import APIRouter, Depends, Request
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
from app.domain.bets.powerups import GetSeasonPowerUps
from app.domain.bets.use_cases import (
    GetSeasonBetQuestions,
    GetSeasonBetAnswers,
    GetSeasonBetResults,
    PatchSeasonBetAnswers,
    SubmitSeasonBetAnswers
)
from app.models.bets import (
    BetAnswerRead,
    BetAnswersPatchRequest,
    BetAnswersSubmitRequest,
    BetQuestionRead,
    BetQuestionOptionRead,
    SeasonBetQuestionsResponse,
    SeasonBetAnswersResponse,
    BetPowerUpRead,
    SeasonBetPowerUpsResponse,
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
    SeasonBetResultsResponse,
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

    repository = SqlAlchemyBetAnswersRepository(db)
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

@router.patch(
    "/seasons/{season_year}/answers",
    response_model=SeasonBetAnswersResponse,
    response_model_exclude_none=True,
)
def patch_season_answers(
    season_year: int,
    payload: BetAnswersPatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> SeasonBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetAnswersRepository(db)
    use_case = PatchSeasonBetAnswers(repository)

    try:
        result = use_case.execute(
            season_year=season_year,
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

    return SeasonBetAnswersResponse(
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

@router.post(
    "/seasons/{season_year}/answers",
    response_model=SeasonBetAnswersResponse,
    response_model_exclude_none=True,
)
def submit_season_answers(
    season_year: int,
    payload: BetAnswersSubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> SeasonBetAnswersResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetAnswersRepository(db)
    use_case = SubmitSeasonBetAnswers(repository)

    try:
        result = use_case.execute(
            season_year=season_year,
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

    return SeasonBetAnswersResponse(
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


@router.get(
    "/seasons/{season_year}/results",
    response_model=SeasonBetResultsResponse,
    response_model_exclude_none=True,
)
def get_season_results(
    season_year: int,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> SeasonBetResultsResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetResultsRepository(db)
    use_case = GetSeasonBetResults(repository)

    try:
        result = use_case.execute(
            season_year=season_year,
            group_id=group.id,
            user_id=user.id,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return SeasonBetResultsResponse(
        kind=result.kind,
        season_year=result.season_year,
        label=result.label,
        scope=BetResultsScopeRead(
            type=result.scope.type,
            season_year=result.scope.season_year,
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
    "/seasons/{season_year}/powerups",
    response_model=SeasonBetPowerUpsResponse,
)
def get_season_powerups(
    season_year: int,
    request: Request,
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> SeasonBetPowerUpsResponse:
    user, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyBetPowerUpsRepository(db)
    use_case = GetSeasonPowerUps(repository)

    try:
        result = use_case.execute(
            group_id=group.id,
            user_id=user.id,
            season_year=season_year,
        )
    except BetsError as exc:
        raise _translate_bets_error(exc, locale=locale) from exc

    return SeasonBetPowerUpsResponse(
        season_year=result.season_year,
        powerups=[
            BetPowerUpRead(
                code=powerup.code,
                name=powerup.name,
                target_mode=powerup.target_mode,
                quantity=powerup.quantity,
                is_enabled=powerup.is_enabled,
                is_restricted=powerup.is_restricted,
                already_used=powerup.already_used,
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
