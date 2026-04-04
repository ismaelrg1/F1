from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyBetQuestionsRepository
from app.api.deps import require_group_member
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    RaceEventNotFoundForBetQuestionsError,
)
from app.domain.bets.use_cases import GetRaceEventBetQuestions
from app.models.bets import (
    BetQuestionRead,
    BetQuestionOptionRead,
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
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> RaceEventBetQuestionsResponse:
    _, group = user_group

    repository = SqlAlchemyBetQuestionsRepository(db)
    use_case = GetRaceEventBetQuestions(repository)

    try:
        result = use_case.execute(
            race_event_public_id=race_event_public_id,
            group_id=group.id,
        )
    except RaceEventNotFoundForBetQuestionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race event not found",
        ) from exc
    except BetContextNotFoundForRaceEventError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet context not found for this group and race event",
        ) from exc

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
