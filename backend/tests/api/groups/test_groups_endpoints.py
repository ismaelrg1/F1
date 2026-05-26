from uuid import uuid4

from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Role, User
from app.db.enums import RoleName
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole


def _create_user(
    db_session,
    *,
    username: str,
    email: str,
    password: str,
    role_name: RoleName | None = None,
) -> User:
    hasher = PasslibPasswordHasher()
    roles = []

    if role_name is not None:
        role = db_session.execute(
            select(Role).where(Role.name == role_name)
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=role_name, description=role_name.value.title())
            db_session.add(role)
            db_session.flush()
        roles = [role]

    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=roles,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_group(
    db_session,
    *,
    name: str,
    teams_enabled: bool = False,
) -> Group:
    group = Group(
        name=name,
        join_code=None,
        is_private=False,
        teams_enabled=teams_enabled,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()
    return group


def _add_membership(
    db_session,
    *,
    user_id: int,
    group_id: int,
    role: GroupRole,
) -> None:
    db_session.add(
        GroupMembership(
            user_id=user_id,
            group_id=group_id,
            role=role,
        )
    )
    db_session.flush()


def test_get_groups_requires_authentication(client) -> None:
    response = client.get("/api/v1/groups")

    assert response.status_code == 401


def test_get_groups_returns_all_groups_for_admin(client, db_session) -> None:
    admin = _create_user(
        db_session,
        username=f"admin_{uuid4().hex[:8]}",
        email=f"admin_{uuid4().hex[:8]}@example.com",
        password="secret123",
        role_name=RoleName.ADMIN,
    )

    alpha_group = _create_group(db_session, name=f"Alpha {uuid4().hex[:4]}", teams_enabled=True)
    zeta_group = _create_group(db_session, name=f"Zeta {uuid4().hex[:4]}", teams_enabled=False)

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": admin.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/groups")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "public_id": str(alpha_group.public_id),
                "name": alpha_group.name,
                "teams_enabled": True,
            },
            {
                "public_id": str(zeta_group.public_id),
                "name": zeta_group.name,
                "teams_enabled": False,
            },
        ]
    }


def test_get_groups_returns_only_owner_and_moderator_groups_for_non_admin(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )

    moderator_group = _create_group(db_session, name=f"Bravo {uuid4().hex[:4]}", teams_enabled=False)
    owner_group = _create_group(db_session, name=f"Charlie {uuid4().hex[:4]}", teams_enabled=True)
    member_group = _create_group(db_session, name=f"Delta {uuid4().hex[:4]}", teams_enabled=True)

    _add_membership(
        db_session,
        user_id=user.id,
        group_id=owner_group.id,
        role=GroupRole.OWNER,
    )
    _add_membership(
        db_session,
        user_id=user.id,
        group_id=moderator_group.id,
        role=GroupRole.MODERATOR,
    )
    _add_membership(
        db_session,
        user_id=user.id,
        group_id=member_group.id,
        role=GroupRole.MEMBER,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/groups")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "public_id": str(moderator_group.public_id),
                "name": moderator_group.name,
                "role": "MODERATOR",
                "teams_enabled": False,
            },
            {
                "public_id": str(owner_group.public_id),
                "name": owner_group.name,
                "role": "OWNER",
                "teams_enabled": True,
            },
        ]
    }
