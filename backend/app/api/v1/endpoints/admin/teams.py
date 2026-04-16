from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminTeamRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.core.permissions import COMPETITION_MANAGE

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateSeasonTeam,
    CreateTeam,
)

from app.models.teams import (
    SeasonTeamCreateRequest,
    SeasonTeamCreateResponse,
    TeamCreateRequest,
    TeamCreateResponse,
)

router = APIRouter()

@router.post(
    "/teams",
    response_model=TeamCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    data: TeamCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> TeamCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminTeamRepository(db)
    use_case = CreateTeam(repository)

    try:
        team = use_case.execute(
            code=data.code,
            name=data.name,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return TeamCreateResponse(
        id=team.id,
        code=team.code,
        name=team.name,
    )


@router.post(
    "/season-teams",
    response_model=SeasonTeamCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_season_team(
    data: SeasonTeamCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> SeasonTeamCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminTeamRepository(db)
    use_case = CreateSeasonTeam(repository)

    try:
        season_team = use_case.execute(
            season_year=data.season_year,
            team_code=data.team_code,
            is_active=data.is_active,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return SeasonTeamCreateResponse(
        season_year=season_team.season_year,
        team_code=season_team.team_code,
        is_active=season_team.is_active,
    )