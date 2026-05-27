import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.betting import BetContext, BetScore
from app.db.competition import (
    Circuit,
    Country,
    EventSession,
    RaceEvent,
    Season,
    TestingEvent as CompetitionTestingEvent,
    TestingEventSession as CompetitionTestingEventSession,
)
from app.db.enums import (
    BetContextKind,
    BetValueType,
    RaceEventStatus,
    RoleName,
    SessionType,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)
from app.db.scoring import OfficialResult
from app.db.scoring.official_result import SourceType
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole


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


def _create_local_user(
    db_session,
    *,
    username: str,
    email: str,
    password: str,
) -> User:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=[],
    )
    db_session.add(user)
    db_session.flush()
    return user


def _add_group_membership(
    db_session,
    *,
    group_id: int,
    user_id: int,
    role: GroupRole,
) -> None:
    db_session.add(
        GroupMembership(
            group_id=group_id,
            user_id=user_id,
            role=role,
        )
    )
    db_session.flush()


def _create_group(db_session, *, name: str) -> Group:
    group = Group(
        name=name,
        join_code=None,
        is_private=False,
        teams_enabled=False,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()
    return group


def _create_race_bet_context_fixture(db_session):
    season = Season(year=2026, is_active=True)
    country = Country(
        iso2=uuid4().hex[:2].upper(),
        name=f"Country {uuid4().hex[:8]}",
        flag_asset_url=None,
    )
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"circuit_{uuid4().hex[:8]}",
        name=f"Circuit {uuid4().hex[:8]}",
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
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 3, 3, 18, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 1, 9, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 1, 9, 55, tzinfo=timezone.utc),
        )
    ]
    db_session.add(race_event)
    db_session.flush()

    group = _create_group(db_session, name=f"group_{uuid4().hex[:8]}")

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Bahrain GP",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    winner_score = BetScore(
        code=f"RACE_WINNER_{uuid4().hex[:8].upper()}",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    fp1_fastest_score = BetScore(
        code=f"FP1_FASTEST_{uuid4().hex[:8].upper()}",
        label="FP1 Fastest",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([winner_score, fp1_fastest_score])
    db_session.flush()

    return {
        "season": season,
        "group": group,
        "race_event": race_event,
        "fp1_session": race_event.event_sessions[0],
        "bet_context": bet_context,
        "winner_score": winner_score,
        "fp1_fastest_score": fp1_fastest_score,
    }


def _create_testing_bet_context_fixture(db_session):
    season = Season(year=2027, is_active=True)
    country = Country(
        iso2=uuid4().hex[:2].upper(),
        name=f"Country {uuid4().hex[:8]}",
        flag_asset_url=None,
    )
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"circuit_{uuid4().hex[:8]}",
        name=f"Circuit {uuid4().hex[:8]}",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing",
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2027, 2, 10, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2027, 2, 12, 18, 0, tzinfo=timezone.utc),
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2027, 2, 10, 8, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2027, 2, 10, 18, 0, tzinfo=timezone.utc),
        )
    ]
    db_session.add(testing_event)
    db_session.flush()

    group = _create_group(db_session, name=f"group_{uuid4().hex[:8]}")

    bet_context = BetContext(
        kind=BetContextKind.PRETESTING,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=testing_event.id,
        label="Pre-Season Testing",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    fastest_score = BetScore(
        code=f"DAY1_FASTEST_{uuid4().hex[:8].upper()}",
        label="Day 1 Fastest",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add(fastest_score)
    db_session.flush()

    return {
        "season": season,
        "group": group,
        "testing_event": testing_event,
        "session": testing_event.sessions[0],
        "bet_context": bet_context,
        "fastest_score": fastest_score,
    }


def _official_results_payload(data, *, value: str = "VER") -> dict:
    return {
        "bet_context_public_id": str(data["bet_context"].public_id),
        "source": "MANUAL",
        "results": [
            {
                "bet_score_code": data["winner_score"].code,
                "value": value,
            }
        ],
    }


def test_create_official_results_for_event_scope(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_create",
        email="admin_official_results_create@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_race_bet_context_fixture(db_session)

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_create", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "source": "MANUAL",
            "results": [
                {
                    "bet_score_code": data["winner_score"].code,
                    "value": "VER",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert item["bet_score_code"] == data["winner_score"].code
    assert item["label"] == "Race Winner"
    assert item["value"] == "VER"
    assert item["source"] == "MANUAL"
    assert "event_session_public_id" not in item
    assert "testing_event_session_public_id" not in item

    row = db_session.execute(
        select(OfficialResult).where(
            OfficialResult.bet_context_id == data["bet_context"].id,
            OfficialResult.event_session_id.is_(None),
            OfficialResult.testing_event_session_id.is_(None),
            OfficialResult.bet_score_id == data["winner_score"].id,
        )
    ).scalar_one()

    assert row.value == "VER"
    assert row.source == SourceType.MANUAL


def test_create_official_results_for_race_session_scope(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_session",
        email="admin_official_results_session@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_race_bet_context_fixture(db_session)

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_session", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "event_session_public_id": str(data["fp1_session"].public_id),
            "source": "FASTF1",
            "results": [
                {
                    "bet_score_code": data["fp1_fastest_score"].code,
                    "value": "LEC",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert item["event_session_public_id"] == str(data["fp1_session"].public_id)
    assert item["bet_score_code"] == data["fp1_fastest_score"].code
    assert item["value"] == "LEC"
    assert item["source"] == "FASTF1"

    row = db_session.execute(
        select(OfficialResult).where(
            OfficialResult.bet_context_id == data["bet_context"].id,
            OfficialResult.event_session_id == data["fp1_session"].id,
            OfficialResult.testing_event_session_id.is_(None),
            OfficialResult.bet_score_id == data["fp1_fastest_score"].id,
        )
    ).scalar_one()

    assert row.value == "LEC"
    assert row.source == SourceType.FASTF1


def test_create_official_results_for_testing_session_scope(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_testing",
        email="admin_official_results_testing@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_testing_bet_context_fixture(db_session)

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_testing", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "testing_event_session_public_id": str(data["session"].public_id),
            "source": "MANUAL",
            "results": [
                {
                    "bet_score_code": data["fastest_score"].code,
                    "value": "NOR",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["testing_event_session_public_id"] == str(data["session"].public_id)
    assert item["bet_score_code"] == data["fastest_score"].code
    assert item["value"] == "NOR"

    row = db_session.execute(
        select(OfficialResult).where(
            OfficialResult.bet_context_id == data["bet_context"].id,
            OfficialResult.event_session_id.is_(None),
            OfficialResult.testing_event_session_id == data["session"].id,
            OfficialResult.bet_score_id == data["fastest_score"].id,
        )
    ).scalar_one()

    assert row.value == "NOR"


def test_create_official_results_returns_conflict_when_scope_already_has_results(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_conflict",
        email="admin_official_results_conflict@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_race_bet_context_fixture(db_session)

    db_session.add(
        OfficialResult(
            bet_context_id=data["bet_context"].id,
            event_session_id=None,
            testing_event_session_id=None,
            bet_score_id=data["winner_score"].id,
            value="VER",
            source=SourceType.MANUAL,
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_conflict", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "source": "MANUAL",
            "results": [
                {
                    "bet_score_code": data["winner_score"].code,
                    "value": "LEC",
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "management.official_results.already_exists"


def test_patch_official_results_updates_existing_scope_results(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_patch",
        email="admin_official_results_patch@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_race_bet_context_fixture(db_session)

    existing = OfficialResult(
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        bet_score_id=data["winner_score"].id,
        value="VER",
        source=SourceType.MANUAL,
    )
    db_session.add(existing)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_patch", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "source": "FASTF1",
            "results": [
                {
                    "bet_score_code": data["winner_score"].code,
                    "value": "HAM",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["bet_score_code"] == data["winner_score"].code
    assert item["value"] == "HAM"
    assert item["source"] == "FASTF1"

    db_session.refresh(existing)
    assert existing.value == "HAM"
    assert existing.source == SourceType.FASTF1


def test_patch_official_results_returns_not_found_when_scope_has_no_existing_results(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_patch_missing",
        email="admin_official_results_patch_missing@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_race_bet_context_fixture(db_session)

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_patch_missing", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "source": "MANUAL",
            "results": [
                {
                    "bet_score_code": data["winner_score"].code,
                    "value": "VER",
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "management.official_results.not_found"


@pytest.mark.parametrize(
    ("group_role", "username"),
    [
        (GroupRole.OWNER, "owner_official_results_create"),
        (GroupRole.MODERATOR, "moderator_official_results_create"),
    ],
)
def test_create_official_results_allows_group_managers(
    client,
    db_session,
    group_role: GroupRole,
    username: str,
) -> None:
    user = _create_local_user(
        db_session,
        username=username,
        email=f"{username}@example.com",
        password="secret123",
    )
    data = _create_race_bet_context_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=user.id,
        role=group_role,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json=_official_results_payload(data),
    )

    assert response.status_code == 201
    assert response.json()["items"][0]["bet_score_code"] == data["winner_score"].code


def test_patch_official_results_allows_group_owner(client, db_session) -> None:
    user = _create_local_user(
        db_session,
        username="owner_official_results_patch",
        email="owner_official_results_patch@example.com",
        password="secret123",
    )
    data = _create_race_bet_context_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=user.id,
        role=GroupRole.OWNER,
    )

    existing = OfficialResult(
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        bet_score_id=data["winner_score"].id,
        value="VER",
        source=SourceType.MANUAL,
    )
    db_session.add(existing)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "owner_official_results_patch", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        "/api/v1/management/official-results",
        json=_official_results_payload(data, value="HAM"),
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["value"] == "HAM"

    db_session.refresh(existing)
    assert existing.value == "HAM"


def test_create_official_results_forbids_group_member(client, db_session) -> None:
    user = _create_local_user(
        db_session,
        username="member_official_results_create",
        email="member_official_results_create@example.com",
        password="secret123",
    )
    data = _create_race_bet_context_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=user.id,
        role=GroupRole.MEMBER,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "member_official_results_create", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json=_official_results_payload(data),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "management.official_results.forbidden_group"


def test_create_official_results_forbids_user_from_other_group(client, db_session) -> None:
    user = _create_local_user(
        db_session,
        username="outsider_official_results_create",
        email="outsider_official_results_create@example.com",
        password="secret123",
    )
    data = _create_race_bet_context_fixture(db_session)
    other_group = _create_group(db_session, name=f"other_group_{uuid4().hex[:8]}")
    _add_group_membership(
        db_session,
        group_id=other_group.id,
        user_id=user.id,
        role=GroupRole.OWNER,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "outsider_official_results_create", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json=_official_results_payload(data),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "management.official_results.forbidden_group"


@pytest.mark.manual
def test_create_official_results_prints_payload(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_manual_create",
        email="admin_official_results_manual_create@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_race_bet_context_fixture(db_session)

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_manual_create", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "event_session_public_id": str(data["fp1_session"].public_id),
            "source": "MANUAL",
            "results": [
                {
                    "bet_score_code": data["fp1_fastest_score"].code,
                    "value": "VER",
                }
            ],
        },
    )

    assert response.status_code == 201
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


@pytest.mark.manual
def test_patch_official_results_prints_payload(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_official_results_manual_patch",
        email="admin_official_results_manual_patch@example.com",
        password="secret123",
        permission_code="SCORING_MANAGE",
    )
    data = _create_race_bet_context_fixture(db_session)

    existing = OfficialResult(
        bet_context_id=data["bet_context"].id,
        event_session_id=data["fp1_session"].id,
        testing_event_session_id=None,
        bet_score_id=data["fp1_fastest_score"].id,
        value="LEC",
        source=SourceType.MANUAL,
    )
    db_session.add(existing)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_official_results_manual_patch", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        "/api/v1/management/official-results",
        json={
            "bet_context_public_id": str(data["bet_context"].public_id),
            "event_session_public_id": str(data["fp1_session"].public_id),
            "source": "FASTF1",
            "results": [
                {
                    "bet_score_code": data["fp1_fastest_score"].code,
                    "value": "HAM",
                }
            ],
        },
    )

    assert response.status_code == 200
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
