from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyGroupRepository
from app.api.deps import get_current_user
from app.db.auth import User
from app.db.enums import RoleName
from app.db.session import get_db
from app.domain.groups import ListVisibleGroups
from app.models.groups import GroupRead, GroupsResponse

router = APIRouter()


@router.get(
    "/groups",
    response_model=GroupsResponse,
    response_model_exclude_none=True,
)
def get_groups(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GroupsResponse:
    repository = SqlAlchemyGroupRepository(db)
    use_case = ListVisibleGroups(repository)

    is_admin = any(role.name == RoleName.ADMIN for role in user.roles)

    groups = use_case.execute(
        user_id=user.id,
        is_admin=is_admin,
    )

    return GroupsResponse(
        items=[
            GroupRead(
                public_id=group.public_id,
                name=group.name,
                role=group.role,
                teams_enabled=group.teams_enabled,
            )
            for group in groups
        ]
    )