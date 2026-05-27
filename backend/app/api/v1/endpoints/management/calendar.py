from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAccessRepository,
    SqlAlchemyManagementCalendarRepository,
)
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.auth import User
from app.db.enums import RoleName
from app.db.session import get_db
from app.db.social.group_membership import GroupRole
from app.domain.access import ResolveCurrentGroup
from app.domain.management.calendar import GetManagementCalendar
from app.models.management_calendar import (
    ManagementCalendarCountryRead,
    ManagementCalendarEventRead,
    ManagementCalendarResponse,
    ManagementCalendarSessionRead,
)

router = APIRouter()


@router.get(
    "/calendar",
    response_model=ManagementCalendarResponse,
    response_model_exclude_none=True,
)
def get_management_calendar(
    request: Request,
    season_year: int | None = Query(default=None),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ManagementCalendarResponse:
    if x_group_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "management.group_required",
                    "message": "X-Group-Id is required.",
                }
            },
        )

    access_repository = SqlAlchemyAccessRepository(db)
    group_ref = ResolveCurrentGroup(
        access_repository,
        default_group_id=settings.default_group_id,
        default_group_public_id=getattr(settings, "default_group_public_id", None),
    ).execute(str(x_group_id))

    is_admin = any(role.name == RoleName.ADMIN for role in user.roles)

    repository = SqlAlchemyManagementCalendarRepository(db)

    if not is_admin:
        role = access_repository.get_group_role(
            user_id=user.id,
            group_id=group_ref.id,
        )
        if role not in {GroupRole.OWNER, GroupRole.MODERATOR}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "management.forbidden_group",
                        "message": "You are not allowed to manage this group.",
                    }
                },
            )

    use_case = GetManagementCalendar(repository)
    results = use_case.execute(
        season_year=season_year,
        group_id=group_ref.id,
    )

    return ManagementCalendarResponse(
        items=[
            ManagementCalendarEventRead(
                type=item.type,
                public_id=item.public_id,
                season_year=item.season_year,
                round_number=item.round_number,
                name=item.name,
                country=ManagementCalendarCountryRead(
                    name=item.country.name,
                    flag_asset_url=item.country.flag_asset_url,
                ),
                sessions=[
                    ManagementCalendarSessionRead(
                        public_id=session.public_id,
                        name=session.name,
                        type=session.type,
                        has_official_results=session.has_official_results,
                        results_published=session.results_published,
                    )
                    for session in item.sessions
                ],
                has_bet_context=item.has_bet_context,
                has_official_results=item.has_official_results,
                results_published=item.results_published,
            )
            for item in results
        ]
    )