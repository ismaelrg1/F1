from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.competition import Season
from app.db.enums import RoleName, SeasonDriverStatus


def _create_admin_user_with_permission(
    db_session,
    *,
    username: str,
    email: str,
    password: str,
    permission_code: str,
) -> None:
    hasher = PasslibPasswordHasher()

    permission = db_session.execute(
        select(Permission).where(Permission.code == permission_code)
    ).scalar_one_or_none()
    if permission is None:
        permission = Permission(code=permission_code, description=permission_code)
        db_session.add(permission)
        db_session.flush()

    role = db_session.execute(
        select(Role).where(Role.name == RoleName.ADMIN)
    ).scalar_one_or_none()
    if role is None:
        role = Role(name=RoleName.ADMIN, description="Admin")
        db_session.add(role)
        db_session.flush()

    if permission not in role.permissions:
        role.permissions.append(permission)

    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=[role],
    )
    db_session.add(user)
    db_session.flush()


def test_create_driver(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_driver",
        email="admin_driver@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_driver", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/drivers",
        json={"code": "ALO", "name": "Fernando Alonso"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "ALO"
    assert payload["name"] == "Fernando Alonso"


def test_create_season_driver(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_season_driver",
        email="admin_season_driver@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )
    db_session.add(Season(year=2026, is_active=True))
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_season_driver", "password": "secret123"},
    )
    assert login_response.status_code == 200

    client.post("/api/v1/admin/drivers", json={"code": "ALO", "name": "Fernando Alonso"})

    response = client.post(
        "/api/v1/admin/season-drivers",
        json={
            "season_year": 2026,
            "driver_code": "ALO",
            "status": SeasonDriverStatus.PRIMARY.value,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["season_year"] == 2026
    assert payload["driver_code"] == "ALO"
    assert payload["status"] == SeasonDriverStatus.PRIMARY.value


def test_create_team(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_team",
        email="admin_team@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_team", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/teams",
        json={"code": "AST", "name": "Aston Martin"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "AST"
    assert payload["name"] == "Aston Martin"


def test_create_season_team(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_season_team",
        email="admin_season_team@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )
    db_session.add(Season(year=2026, is_active=True))
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_season_team", "password": "secret123"},
    )
    assert login_response.status_code == 200

    client.post("/api/v1/admin/teams", json={"code": "AST", "name": "Aston Martin"})

    response = client.post(
        "/api/v1/admin/season-teams",
        json={
            "season_year": 2026,
            "team_code": "AST",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["season_year"] == 2026
    assert payload["team_code"] == "AST"
    assert payload["is_active"] is True


def test_create_engine(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_engine",
        email="admin_engine@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_engine", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/engines",
        json={"code": "MERCEDES", "name": "Mercedes"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "MERCEDES"
    assert payload["name"] == "Mercedes"


def test_create_season_engine(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_season_engine",
        email="admin_season_engine@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )
    db_session.add(Season(year=2026, is_active=True))
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_season_engine", "password": "secret123"},
    )
    assert login_response.status_code == 200

    client.post("/api/v1/admin/engines", json={"code": "MERCEDES", "name": "Mercedes"})

    response = client.post(
        "/api/v1/admin/season-engines",
        json={
            "season_year": 2026,
            "engine_code": "MERCEDES",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["season_year"] == 2026
    assert payload["engine_code"] == "MERCEDES"
    assert payload["is_active"] is True