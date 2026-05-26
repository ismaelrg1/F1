from fastapi import APIRouter, Depends,  Header, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyAccessRepository, SqlAlchemyAdminBetContextRepository
from app.api.deps import get_current_user, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.enums import RoleName
from app.db.session import get_db
from app.db.social.group_membership import GroupRole
from app.domain.access import ResolveCurrentGroup
from app.domain.admin import AdminError, GenerateBetContexts
from app.domain.admin.bet_contexts.errors import (
    BetContextGenerationForbiddenGroupError,
    BetContextGenerationGroupScopeRequiredError,
)
from app.models.bet_contexts import (
    AdminBetContextGenerateRequest,
    AdminBetContextGenerateResponse,
)

router = APIRouter()


@router.post(
    "/bet-contexts/generate",
    response_model=AdminBetContextGenerateResponse,
    status_code=status.HTTP_200_OK,
)
def generate_bet_contexts(
    data: AdminBetContextGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    x_group_id: str | None = Header(default=None),
    user: User = Depends(get_current_user),
) -> AdminBetContextGenerateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminBetContextRepository(db)
    use_case = GenerateBetContexts(repository)

    try:
        resolved_group_id = _resolve_generation_group_id(
            db=db,
            repository=repository,
            user=user,
            raw_group_public_id=x_group_id,
        )

        result = use_case.execute(
            season_id=data.season_id,
            group_id=resolved_group_id,
            include_season=data.include_season,
            include_race_events=data.include_race_events,
            include_testing_events=data.include_testing_events,
        )
        db.commit()
    except AdminError as exc:
        db.rollback()
        raise _translate_admin_error(exc, locale=locale) from exc

    return AdminBetContextGenerateResponse(
        groups_processed=result.groups_processed,
        created=result.created,
        existing=result.existing,
        season_contexts_created=result.season_contexts_created,
        race_event_contexts_created=result.race_event_contexts_created,
        testing_event_contexts_created=result.testing_event_contexts_created,
    )

def _resolve_generation_group_id(
    *,
    db: Session,
    repository: SqlAlchemyAdminBetContextRepository,
    user: User,
    raw_group_public_id: str | None,
) -> int | None:
    is_admin = any(role.name == RoleName.ADMIN for role in user.roles)

    if raw_group_public_id is None:
        if is_admin:
            return None
        raise BetContextGenerationGroupScopeRequiredError()

    access_repository = SqlAlchemyAccessRepository(db)
    resolver = ResolveCurrentGroup(
        access_repository,
        default_group_id=None,
        default_group_public_id=None,
    )
    group = resolver.execute(raw_group_public_id)

    if is_admin:
        return group.id

    group_role = repository.get_group_role(
        user_id=user.id,
        group_id=group.id,
    )
    if group_role not in {GroupRole.OWNER, GroupRole.MODERATOR}:
        raise BetContextGenerationForbiddenGroupError()

    return group.id