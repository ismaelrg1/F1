from app.domain.groups.models import VisibleGroupResult
from app.domain.groups.ports import GroupRepository


class ListVisibleGroups:
    def __init__(self, repository: GroupRepository):
        self._repository = repository

    def execute(
        self,
        *,
        user_id: int,
        is_admin: bool,
    ) -> list[VisibleGroupResult]:
        return self._repository.list_visible_groups_for_user(
            user_id=user_id,
            is_admin=is_admin,
        )