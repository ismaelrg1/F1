from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.auth import Role, User
from app.db.social import Group, GroupMembership
from app.domain.access.models import AccessGroup, AuthenticatedUser
from app.domain.access.ports import AccessRepository


class SqlAlchemyAccessRepository(AccessRepository):
    def __init__(self, session: Session):
        self._session = session


    def get_authenticated_user_by_public_id(self, public_id: UUID) -> AuthenticatedUser | None:
        stmt = (
            select(User)
            .where(User.public_id == public_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        user = self._session.execute(stmt).scalar_one_or_none()
        if user is None:
            return None

        role = user.roles[0].name.value if user.roles else None
        permission_codes = frozenset(
            permission.code
            for role_item in (user.roles or [])
            for permission in (role_item.permissions or [])
        )
        return AuthenticatedUser(
            id=user.id,
            public_id=user.public_id,
            role=role,
            permission_codes=permission_codes,
        )
    
    def get_group_by_public_id(self, public_id: UUID) -> AccessGroup | None:
        stmt = select(Group).where(Group.public_id == public_id)
        group = self._session.execute(stmt).scalar_one_or_none()
        if group is None:
            return None
        return AccessGroup(id=group.id, public_id=group.public_id)

    def get_group_by_id(self, group_id: int) -> AccessGroup | None:
        group = self._session.get(Group, group_id)
        if group is None:
            return None
        return AccessGroup(id=group.id, public_id=group.public_id)

    def is_group_member(self, user_id: int, group_id: int) -> bool:
        stmt = select(GroupMembership.id).where(
            GroupMembership.user_id == user_id,
            GroupMembership.group_id == group_id,
        )
        membership_id = self._session.execute(stmt).scalar_one_or_none()
        return membership_id is not None

    def get_group_role(self, *, user_id: int, group_id: int):
        stmt = select(GroupMembership.role).where(
            GroupMembership.user_id == user_id,
            GroupMembership.group_id == group_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()
