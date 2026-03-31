from datetime import datetime, timezone

from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.competition import Circuit, Country, EventSession, RaceEvent, Season
from app.db.enums import RaceEventStatus, RoleName, SessionType, SourceProvider


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


def test_list_admin_race_events_requires_auth(client) -> None:
    response = client.get("/api/v1/admin/race-events")
    assert response.status_code == 401


def test_list_admin_race_events_returns_items(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_race_read",
        email="admin_race_read@example.com",
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

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Spanish Grand Prix",
        source_provider=SourceProvider.FASTF1,
        source_key="fastf1:race:2026:formula-1-spanish-grand-prix-2026:barcelona",
        scheduled_event_start=datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 5, 31, 16, 0, tzinfo=timezone.utc),
        status=RaceEventStatus.SCHEDULED,
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.FASTF1,
            source_key="fastf1:race:2026:formula-1-spanish-grand-prix-2026:barcelona:fp1",
            start_datetime=datetime(2026, 5, 29, 11, 30, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 5, 29, 11, 30, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 5, 29, 11, 25, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 5, 29, 11, 25, tzinfo=timezone.utc),
            status=RaceEventStatus.SCHEDULED,
        )
    ]
    db_session.add(race_event)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_race_read", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/race-events?season_year=2026")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["season_year"] == 2026
    assert item["round_number"] == 1
    assert item["circuit_code"] == "barcelona"
    assert item["source_provider"] == "FASTF1"
    assert item["source_key"] == "fastf1:race:2026:formula-1-spanish-grand-prix-2026:barcelona"
    assert len(item["sessions"]) == 1
    assert item["sessions"][0]["session_type"] == "FP1"
    assert item["sessions"][0]["source_provider"] == "FASTF1"