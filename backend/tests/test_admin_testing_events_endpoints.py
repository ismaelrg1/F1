from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.competition import Circuit, Country, Season
from app.db.enums import RoleName


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


def test_create_testing_event(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_testing",
        email="admin_testing@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    season = Season(year=2026, is_active=False)
    country = Country(iso2="ES", name="Spain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="barcelona",
        name="Circuit de Barcelona-Catalunya",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_testing", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/testing-events",
        json={
            "season_year": 2026,
            "circuit_code": "barcelona",
            "name": "Pre-Season Testing 1",
            "scheduled_event_start": "2026-02-11T07:00:00Z",
            "scheduled_event_end": "2026-02-13T17:00:00Z",
            "sessions": [
                {
                    "session_order": 1,
                    "name": "Day 1",
                    "scheduled_start_datetime": "2026-02-11T07:00:00Z",
                    "scheduled_end_datetime": "2026-02-11T17:00:00Z",
                },
                {
                    "session_order": 2,
                    "name": "Day 2",
                    "scheduled_start_datetime": "2026-02-12T07:00:00Z",
                    "scheduled_end_datetime": "2026-02-12T17:00:00Z",
                },
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["season_year"] == 2026
    assert payload["circuit_code"] == "barcelona"
    assert len(payload["sessions"]) == 2
    assert payload["sessions"][0]["session_order"] == 1


def test_create_testing_event_returns_conflict_for_duplicate(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_testing_duplicate",
        email="admin_testing_duplicate@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    season = Season(year=2026, is_active=False)
    country = Country(iso2="ES", name="Spain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="barcelona",
        name="Circuit de Barcelona-Catalunya",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_testing_duplicate", "password": "secret123"},
    )
    assert login_response.status_code == 200

    payload = {
        "season_year": 2026,
        "circuit_code": "barcelona",
        "name": "Pre-Season Testing 1",
        "scheduled_event_start": "2026-02-11T07:00:00Z",
        "scheduled_event_end": "2026-02-13T17:00:00Z",
        "sessions": [
            {
                "session_order": 1,
                "name": "Day 1",
                "scheduled_start_datetime": "2026-02-11T07:00:00Z",
                "scheduled_end_datetime": "2026-02-11T17:00:00Z",
            }
        ],
    }

    first_response = client.post("/api/v1/admin/testing-events", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/api/v1/admin/testing-events", json=payload)
    assert second_response.status_code == 409
