from typing import Protocol

from app.domain.groups.models import VisibleGroupResult


class GroupRepository(Protocol):
    def list_visible_groups_for_user(
        self,
        *,
        user_id: int,
        is_admin: bool,
    ) -> list[VisibleGroupResult]:
        ...