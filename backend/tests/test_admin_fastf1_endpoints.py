import pytest

from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.competition import Country
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
        permission = Permission(
            code=permission_code,
            description=f"{permission_code} permission for tests",
        )
        db_session.add(permission)
        db_session.flush()

    role = db_session.execute(
        select(Role).where(Role.name == RoleName.ADMIN)
    ).scalar_one_or_none()

    if role is None:
        role = Role(
            name=RoleName.ADMIN,
            description="Admin role for tests",
        )
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


class FakeSchedule:
    def iterrows(self):
        yield 0, {
            "EventFormat": "conventional",
            "RoundNumber": 1,
            "Country": "Spain",
            "EventName": "Spanish Grand Prix",
            "OfficialEventName": "Formula 1 Spanish Grand Prix 2026",
            "Location": "Barcelona",
            "EventDate": None,
            "Session1": "Practice 1",
            "Session1DateUtc": None,
            "Session2": "Practice 2",
            "Session2DateUtc": None,
            "Session3": "Practice 3",
            "Session3DateUtc": None,
            "Session4": "Qualifying",
            "Session4DateUtc": None,
            "Session5": "Race",
            "Session5DateUtc": None,
        }

        yield 1, {
            "EventFormat": "testing",
            "RoundNumber": 0,
            "Country": "Bahrain",
            "EventName": "Pre-Season Testing",
            "OfficialEventName": "Formula 1 Pre-Season Testing 2026",
            "Location": "Sakhir",
            "EventDate": None,
            "Session1": "Practice 1",
            "Session1DateUtc": None,
            "Session2": None,
            "Session2DateUtc": None,
            "Session3": None,
            "Session3DateUtc": None,
            "Session4": None,
            "Session4DateUtc": None,
            "Session5": None,
            "Session5DateUtc": None,
        }


def test_list_fastf1_race_events_returns_non_testing_events(client, db_session, monkeypatch) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_fastf1",
        email="admin_fastf1@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    db_session.add(Country(iso2="ES", name="Spain", flag_asset_url=None))
    db_session.flush()

    monkeypatch.setattr(
        "app.adapters.fastf1.admin_fastf1_repository.fastf1.get_event_schedule",
        lambda year: FakeSchedule(),
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_fastf1", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/fastf1/race-events/2026")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["items"]) == 1
    assert payload["items"][0]["country_iso2_suggestion"] == "ES"
    assert payload["items"][0]["circuit_code_suggestion"] == "barcelona"
    assert [session["session_type"] for session in payload["items"][0]["sessions"]] == [
        "FP1",
        "FP2",
        "FP3",
        "QUALY",
        "RACE",
    ]


import json

@pytest.mark.manual
def test_preview_fastf1_race_events_prints_payload(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_fastf1_preview",
        email="admin_fastf1_preview@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_fastf1_preview", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/fastf1/race-events/2026")
    assert response.status_code == 200

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

@pytest.mark.manual
def test_preview_fastf1_testing_events_prints_payload(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_fastf1_testing_preview",
        email="admin_fastf1_testing_preview@example.com",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_fastf1_testing_preview", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/fastf1/testing-events/2026")
    assert response.status_code == 200

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))