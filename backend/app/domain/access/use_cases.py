from uuid import UUID

from app.domain.access.errors import (
    GroupNotFoundError,
    InvalidGroupIdError,
    InvalidSubjectError,
    MissingPermissionsError,
    MissingSubjectError,
    NotGroupMemberError,
    UserNotFoundError,
)
from app.domain.access.models import AccessGroup, AuthenticatedUser
from app.domain.access.ports import AccessRepository


class ResolveCurrentUser:
    def __init__(self, repository: AccessRepository):
        self._repository = repository

    def execute(self, subject: str | None) -> AuthenticatedUser:
        if not subject:
            raise MissingSubjectError()

        try:
            user_public_id = UUID(subject)
        except (TypeError, ValueError) as exc:
            raise InvalidSubjectError() from exc

        user = self._repository.get_authenticated_user_by_public_id(user_public_id)
        if user is None:
            raise UserNotFoundError()
        return user


class ResolveCurrentGroup:
    def __init__(
        self,
        repository: AccessRepository,
        *,
        default_group_id: int | None = None,
        default_group_public_id: UUID | None = None,
    ):
        self._repository = repository
        self._default_group_id = default_group_id
        self._default_group_public_id = default_group_public_id

    def execute(self, raw_group_id: str | None) -> AccessGroup:
        if raw_group_id is None:
            if self._default_group_public_id is not None:
                group = self._repository.get_group_by_public_id(self._default_group_public_id)
            elif self._default_group_id is not None:
                group = self._repository.get_group_by_id(self._default_group_id)
            else:
                group = None

        else:
            try:
                group_public_id = UUID(raw_group_id)
            except (TypeError, ValueError) as exc:
                raise InvalidGroupIdError() from exc

            group = self._repository.get_group_by_public_id(group_public_id)

        if group is None:
            raise GroupNotFoundError()
        return group


class EnsureGroupMember:
    def __init__(self, repository: AccessRepository):
        self._repository = repository

    def execute(self, user: AuthenticatedUser, group: AccessGroup) -> tuple[AuthenticatedUser, AccessGroup]:
        if not self._repository.is_group_member(user.id, group.id):
            raise NotGroupMemberError()
        return user, group


class EnsurePermissions:
    def execute_all(self, user: AuthenticatedUser, required: tuple[str, ...]) -> AuthenticatedUser:
        missing = [permission for permission in required if permission not in user.permission_codes]
        if missing:
            raise MissingPermissionsError(missing, require_all=True)
        return user

    def execute_any(self, user: AuthenticatedUser, required: tuple[str, ...]) -> AuthenticatedUser:
        if any(permission in user.permission_codes for permission in required):
            return user
        raise MissingPermissionsError(list(required), require_all=False)
