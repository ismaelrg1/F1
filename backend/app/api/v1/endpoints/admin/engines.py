from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminEngineRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.core.permissions import COMPETITION_MANAGE

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateEngine,
    CreateSeasonEngine,
)

from app.models.engines import (
    EngineCreateRequest,
    EngineCreateResponse,
    SeasonEngineCreateRequest,
    SeasonEngineCreateResponse,
)

router = APIRouter()

@router.post(
    "/engines",
    response_model=EngineCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_engine(
    data: EngineCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> EngineCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminEngineRepository(db)
    use_case = CreateEngine(repository)

    try:
        engine = use_case.execute(
            code=data.code,
            name=data.name,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return EngineCreateResponse(
        id=engine.id,
        code=engine.code,
        name=engine.name,
    )


@router.post(
    "/season-engines",
    response_model=SeasonEngineCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_season_engine(
    data: SeasonEngineCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> SeasonEngineCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminEngineRepository(db)
    use_case = CreateSeasonEngine(repository)

    try:
        season_engine = use_case.execute(
            season_year=data.season_year,
            engine_code=data.engine_code,
            is_active=data.is_active,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return SeasonEngineCreateResponse(
        season_year=season_engine.season.year,
        engine_code=season_engine.engine.code,
        is_active=season_engine.is_active,
    )
