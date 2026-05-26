from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole
from app.domain.groups.models import VisibleGroupResult
from app.domain.groups.ports import GroupRepository


class SqlAlchemyGroupRepository(GroupRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_visible_groups_for_user(
        self,
        *,
        user_id: int,
        is_admin: bool,
    ) -> list[VisibleGroupResult]:
        if is_admin:
            stmt = (
                select(Group)
                .order_by(Group.name.asc())
            )

            groups = self._session.execute(stmt).scalars().all()

            return [
                VisibleGroupResult(
                    public_id=group.public_id,
                    name=group.name,
                    role=None,
                    teams_enabled=group.teams_enabled,
                )
                for group in groups
            ]

        stmt = (
            select(Group, GroupMembership.role)
            .join(GroupMembership, GroupMembership.group_id == Group.id)
            .where(
                GroupMembership.user_id == user_id,
                GroupMembership.role.in_([GroupRole.OWNER, GroupRole.MODERATOR]),
            )
            .order_by(Group.name.asc())
        )

        rows = self._session.execute(stmt).all()

        return [
            VisibleGroupResult(
                public_id=group.public_id,
                name=group.name,
                role=role.value,
                teams_enabled=group.teams_enabled,
            )
            for group, role in rows
        ]