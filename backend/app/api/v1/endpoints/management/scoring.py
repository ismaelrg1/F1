from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy.management.scoring_repository import SqlAlchemyManagementScoringRepository
from app.api.deps import (
    get_current_user,
    resolve_management_group_id,
    _translate_management_error,
)
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.domain.management import ManagementError

from app.domain.management.scoring import (
    CalculateRaceEventScoring,
    CalculateSeasonScoring,
    CalculateTestingEventScoring,
)
from app.models.management_scoring import ScoringCalculationResponse

router = APIRouter()


@router.post(
    "/scoring/race-events/{race_event_public_id}/calculate",
    response_model=ScoringCalculationResponse,
)
def calculate_race_event_scoring(
    race_event_public_id: UUID,
    request: Request,
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScoringCalculationResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
    )

    repository = SqlAlchemyManagementScoringRepository(db)

    try:
        result = CalculateRaceEventScoring(repository).execute(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return ScoringCalculationResponse.model_validate(result)


@router.post(
    "/scoring/testing-events/{testing_event_public_id}/calculate",
    response_model=ScoringCalculationResponse,
)
def calculate_testing_event_scoring(
    testing_event_public_id: UUID,
    request: Request,
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScoringCalculationResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
    )

    repository = SqlAlchemyManagementScoringRepository(db)

    try:
        result = CalculateTestingEventScoring(repository).execute(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return ScoringCalculationResponse.model_validate(result)


@router.post(
    "/scoring/seasons/{season_year}/calculate",
    response_model=ScoringCalculationResponse,
)
def calculate_season_scoring(
    season_year: int,
    request: Request,
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScoringCalculationResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
    )

    repository = SqlAlchemyManagementScoringRepository(db)

    try:
        result = CalculateSeasonScoring(repository).execute(
            group_id=group_id,
            season_year=season_year,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return ScoringCalculationResponse.model_validate(result)
