from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminSeasonRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.core.permissions import COMPETITION_MANAGE

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateSeason,
    ListSeasons,
)

from app.models.seasons import ( 
    SeasonCreateRequest, 
    SeasonCreateResponse,
    SeasonListResponse,
    SeasonRead,
)

router = APIRouter()

@router.post(
    "/seasons",
    response_model=SeasonCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_season(
    data: SeasonCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> SeasonCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminSeasonRepository(db)
    use_case = CreateSeason(repository)

    try:
        season = use_case.execute(
            year=data.year,
            is_active=data.is_active,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return SeasonCreateResponse(
        id=season.id,
        year=season.year,
        is_active=season.is_active,
    )

@router.get(
    "seasons",
    response_model=SeasonListResponse,
    status_code=status.HTTP_200_OK,
)
def get_seasons(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE))
) -> SeasonListResponse:
    repository = SqlAlchemyAdminSeasonRepository(db)
    use_case = ListSeasons(repository)

    seasons = use_case.execute()

    return SeasonListResponse(
        items=[
            SeasonRead(
                id=season.id,
                year=season.year,
                is_active=season.is_active,
            )
            for season in seasons
        ]
    )
