from typing import Protocol
from uuid import UUID

from app.domain.access.models import AccessGroup, AuthenticatedUser


class AccessRepository(Protocol):
    def get_authenticated_user_by_public_id(self, public_id: UUID) -> AuthenticatedUser | None:
        ...

    def get_group_by_public_id(self, public_id: UUID) -> AccessGroup | None:
        ...

    def get_group_by_id(self, group_id: int) -> AccessGroup | None:
        ...

    def is_group_member(self, user_id: int, group_id: int) -> bool:
        ...

    def get_group_role(self, *, user_id: int, group_id: int):
        ...
