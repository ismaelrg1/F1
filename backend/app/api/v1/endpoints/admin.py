from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

import logging

from app.adapters.sqlalchemy import SqlAlchemySeasonRepository
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    PublishResults,
    AdminError,
    CreateSeason,
)
from app.models.seasons import SeasonCreateRequest, SeasonCreateResponse


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/results/publish")
def publish_results(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("RESULTS_PUBLISH")),
):
    return PublishResults().execute(user.id)


@router.post(
        "/seasons",
        response_model=SeasonCreateResponse,
        status_code=status.HTTP_201_CREATED
)
def create_season(
    data: SeasonCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE"))

) -> SeasonCreateResponse:
    
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemySeasonRepository(db)
    use_case = CreateSeason(repository)

    try:
        season = use_case.execute(
            year=data.year,
            is_active=data.is_active,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return SeasonCreateResponse.model_validate(season)
