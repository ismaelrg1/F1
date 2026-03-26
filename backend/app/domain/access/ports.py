from typing import Protocol

from app.domain.access.models import AccessGroup, AuthenticatedUser


class AccessRepository(Protocol):
    def get_authenticated_user(self, user_id: int) -> AuthenticatedUser | None:
        ...

    def get_group(self, group_id: int) -> AccessGroup | None:
        ...

    def is_group_member(self, user_id: int, group_id: int) -> bool:
        ...
