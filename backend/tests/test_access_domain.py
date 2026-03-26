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
from app.domain.access.use_cases import (
    EnsureGroupMember,
    EnsurePermissions,
    ResolveCurrentGroup,
    ResolveCurrentUser,
)


class FakeAccessRepository:
    def __init__(self):
        self.users: dict[int, AuthenticatedUser] = {}
        self.groups: dict[int, AccessGroup] = {}
        self.memberships: set[tuple[int, int]] = set()

    def get_authenticated_user(self, user_id: int) -> AuthenticatedUser | None:
        return self.users.get(user_id)

    def get_group(self, group_id: int) -> AccessGroup | None:
        return self.groups.get(group_id)

    def is_group_member(self, user_id: int, group_id: int) -> bool:
        return (user_id, group_id) in self.memberships


def test_resolve_current_user_requires_subject() -> None:
    repository = FakeAccessRepository()
    use_case = ResolveCurrentUser(repository)

    try:
        use_case.execute(None)
    except MissingSubjectError:
        pass
    else:
        raise AssertionError("MissingSubjectError was not raised")


def test_resolve_current_user_rejects_invalid_subject() -> None:
    repository = FakeAccessRepository()
    use_case = ResolveCurrentUser(repository)

    try:
        use_case.execute("abc")
    except InvalidSubjectError:
        pass
    else:
        raise AssertionError("InvalidSubjectError was not raised")


def test_resolve_current_user_requires_existing_user() -> None:
    repository = FakeAccessRepository()
    use_case = ResolveCurrentUser(repository)

    try:
        use_case.execute("1")
    except UserNotFoundError:
        pass
    else:
        raise AssertionError("UserNotFoundError was not raised")


def test_resolve_current_group_uses_default_group() -> None:
    repository = FakeAccessRepository()
    repository.groups[1] = AccessGroup(id=1)
    use_case = ResolveCurrentGroup(repository, default_group_id=1)

    group = use_case.execute(None)

    assert group.id == 1


def test_resolve_current_group_rejects_invalid_group_id() -> None:
    repository = FakeAccessRepository()
    use_case = ResolveCurrentGroup(repository, default_group_id=1)

    try:
        use_case.execute("bad")
    except InvalidGroupIdError:
        pass
    else:
        raise AssertionError("InvalidGroupIdError was not raised")


def test_resolve_current_group_requires_existing_group() -> None:
    repository = FakeAccessRepository()
    use_case = ResolveCurrentGroup(repository, default_group_id=1)

    try:
        use_case.execute("10")
    except GroupNotFoundError:
        pass
    else:
        raise AssertionError("GroupNotFoundError was not raised")


def test_ensure_group_member_requires_membership() -> None:
    repository = FakeAccessRepository()
    use_case = EnsureGroupMember(repository)
    user = AuthenticatedUser(id=1, role="USER", permission_codes=frozenset())
    group = AccessGroup(id=2)

    try:
        use_case.execute(user, group)
    except NotGroupMemberError:
        pass
    else:
        raise AssertionError("NotGroupMemberError was not raised")


def test_ensure_permissions_all_requires_all_codes() -> None:
    use_case = EnsurePermissions()
    user = AuthenticatedUser(id=1, role="ADMIN", permission_codes=frozenset({"A"}))

    try:
        use_case.execute_all(user, ("A", "B"))
    except MissingPermissionsError as exc:
        assert exc.missing_permissions == ["B"]
    else:
        raise AssertionError("MissingPermissionsError was not raised")


def test_ensure_permissions_any_accepts_one_code() -> None:
    use_case = EnsurePermissions()
    user = AuthenticatedUser(id=1, role="ADMIN", permission_codes=frozenset({"A"}))

    resolved = use_case.execute_any(user, ("B", "A"))

    assert resolved.id == 1
