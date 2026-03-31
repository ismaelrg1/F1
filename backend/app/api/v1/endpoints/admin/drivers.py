from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminDriverRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateDriver,
    CreateSeasonDriver,
)

from app.models.drivers import (
    DriverCreateRequest,
    DriverCreateResponse,
    SeasonDriverCreateRequest,
    SeasonDriverCreateResponse,
)

router = APIRouter()

@router.post(
    "/drivers",
    response_model=DriverCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_driver(
    data: DriverCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> DriverCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminDriverRepository(db)
    use_case = CreateDriver(repository)

    try:
        driver = use_case.execute(
            code=data.code,
            name=data.name,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return DriverCreateResponse(
        id=driver.id,
        code=driver.code,
        name=driver.name,
    )


@router.post(
    "/season-drivers",
    response_model=SeasonDriverCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_season_driver(
    data: SeasonDriverCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> SeasonDriverCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminDriverRepository(db)
    use_case = CreateSeasonDriver(repository)

    try:
        season_driver = use_case.execute(
            season_year=data.season_year,
            driver_code=data.driver_code,
            status=data.status,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return SeasonDriverCreateResponse(
        season_year=season_driver.season.year,
        driver_code=season_driver.driver.code,
        status=season_driver.status,
    )