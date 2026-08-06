from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.betting import BetContext
from app.db.competition import (
    Circuit,
    Country,
    RaceEvent,
    Season,
    TestingEvent as CompetitionTestingEvent,
)
from app.db.enums import (
    BetContextKind,
    RaceEventStatus,
    RoleName,
    TestingEventStatus as CompetitionTestingEventStatus,
)
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole

def _create_admin_user_with_permission(
    db_session,
    *,
    username: str,
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
    password: str,
) -> User:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
    )
    db_session.add(user)
    db_session.flush()
    return user


def _add_group_membership(
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


def test_create_season_endpoint_creates_season(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_create_season",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_create_season", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/seasons",
        json={"year": 2027, "is_active": False},
    )

    assert response.status_code == 201
    assert response.json()["year"] == 2027
    assert response.json()["is_active"] is False

    season = db_session.execute(
        select(Season).where(Season.year == 2027)
    ).scalar_one()
    assert season.year == 2027
    assert season.is_active is False


def test_create_season_endpoint_returns_conflict_for_duplicate_year(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_duplicate_season",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    db_session.add(Season(year=2027, is_active=False))
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_duplicate_season", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/seasons",
        json={"year": 2027, "is_active": False},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "admin.season_already_exists"


def test_create_season_endpoint_returns_conflict_when_active_season_exists(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_active_season",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    db_session.add(Season(year=2026, is_active=True))
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_active_season", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/seasons",
        json={"year": 2027, "is_active": True},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "admin.active_season_already_exists"


def test_get_seasons_endpoint_lists_seasons_and_filters_by_is_active(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_list_seasons",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    db_session.add_all(
        [
            Season(year=2024, is_active=False),
            Season(year=2026, is_active=True),
            Season(year=2025, is_active=False),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_list_seasons", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/seasons")

    assert response.status_code == 200
    payload = response.json()
    assert [item["year"] for item in payload["items"]] == [2026, 2025, 2024]
    assert [item["is_active"] for item in payload["items"]] == [True, False, False]
    assert all("id" in item for item in payload["items"])

    active_response = client.get("/api/v1/admin/seasons?is_active=true")

    assert active_response.status_code == 200
    active_payload = active_response.json()
    assert len(active_payload["items"]) == 1
    assert active_payload["items"][0]["year"] == 2026
    assert active_payload["items"][0]["is_active"] is True
    assert "id" in active_payload["items"][0]


def test_patch_season_endpoint_activates_requested_season_and_deactivates_previous_one(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_patch_season",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    previous_active = Season(year=2025, is_active=True)
    target = Season(year=2026, is_active=False)
    db_session.add_all([previous_active, target])
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_patch_season", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/admin/seasons/{target.id}",
        json={"is_active": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": target.id,
        "year": 2026,
        "is_active": True,
    }

    refreshed_previous = db_session.execute(
        select(Season).where(Season.id == previous_active.id)
    ).scalar_one()
    refreshed_target = db_session.execute(
        select(Season).where(Season.id == target.id)
    ).scalar_one()

    assert refreshed_previous.is_active is False
    assert refreshed_target.is_active is True


def test_patch_season_endpoint_returns_not_found_for_missing_season(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_patch_missing_season",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_patch_missing_season", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        "/api/v1/admin/seasons/999999",
        json={"is_active": True},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "admin.season_not_found"


def test_generate_bet_contexts_endpoint_creates_contexts_and_is_idempotent(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_generate_bet_contexts",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    group = Group(
        name="Bet Context Group",
        is_private=True,
        teams_enabled=False,
        max_team_size=None,
    )
    season = Season(year=2030, is_active=False)
    country = Country(
        iso2="GB",
        name="United Kingdom",
        flag_asset_url=None,
    )
    db_session.add_all([group, season, country])
    db_session.flush()

    circuit = Circuit(
        code="silverstone",
        name="Silverstone Circuit",
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
        name="British Grand Prix",
        status=RaceEventStatus.SCHEDULED,
    )
    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="British Pre-Season Testing",
        status=CompetitionTestingEventStatus.SCHEDULED,
    )
    db_session.add_all([race_event, testing_event])
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_generate_bet_contexts", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/bet-contexts/generate",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "season_id": season.id,
            "include_season": True,
            "include_race_events": True,
            "include_testing_events": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "groups_processed": 1,
        "created": 3,
        "existing": 0,
        "season_contexts_created": 1,
        "race_event_contexts_created": 1,
        "testing_event_contexts_created": 1,
    }

    contexts = db_session.execute(
        select(BetContext)
        .where(BetContext.group_id == group.id)
        .order_by(BetContext.kind.asc())
    ).scalars().all()
    assert len(contexts) == 3

    season_context = next(context for context in contexts if context.kind == BetContextKind.SEASON)
    race_context = next(context for context in contexts if context.kind == BetContextKind.GP)
    testing_context = next(context for context in contexts if context.kind == BetContextKind.PRETESTING)

    assert season_context.season_id == season.id
    assert season_context.race_event_id is None
    assert season_context.testing_event_id is None
    assert season_context.label == f"Season {season.id}"

    assert race_context.season_id == season.id
    assert race_context.race_event_id == race_event.id
    assert race_context.testing_event_id is None
    assert race_context.label == "British Grand Prix"

    assert testing_context.season_id == season.id
    assert testing_context.race_event_id is None
    assert testing_context.testing_event_id == testing_event.id
    assert testing_context.label == "British Pre-Season Testing"

    second_response = client.post(
        "/api/v1/admin/bet-contexts/generate",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "season_id": season.id,
            "include_season": True,
            "include_race_events": True,
            "include_testing_events": True,
        },
    )

    assert second_response.status_code == 200
    assert second_response.json() == {
        "groups_processed": 1,
        "created": 0,
        "existing": 3,
        "season_contexts_created": 0,
        "race_event_contexts_created": 0,
        "testing_event_contexts_created": 0,
    }

    total_contexts = db_session.execute(
        select(BetContext).where(BetContext.group_id == group.id)
    ).scalars().all()
    assert len(total_contexts) == 3


def test_generate_bet_contexts_endpoint_without_group_header_processes_all_groups_for_admin(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_generate_all_bet_contexts",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    first_group = Group(
        name="First Bet Context Group",
        is_private=True,
        teams_enabled=False,
        max_team_size=None,
    )
    second_group = Group(
        name="Second Bet Context Group",
        is_private=True,
        teams_enabled=False,
        max_team_size=None,
    )
    season = Season(year=2031, is_active=False)
    country = Country(
        iso2="IT",
        name="Italy",
        flag_asset_url=None,
    )
    db_session.add_all([first_group, second_group, season, country])
    db_session.flush()

    circuit = Circuit(
        code="monza",
        name="Autodromo Nazionale Monza",
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
        name="Italian Grand Prix",
        status=RaceEventStatus.SCHEDULED,
    )
    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Italian Pre-Season Testing",
        status=CompetitionTestingEventStatus.SCHEDULED,
    )
    db_session.add_all([race_event, testing_event])
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_generate_all_bet_contexts", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/bet-contexts/generate",
        json={
            "season_id": season.id,
            "include_season": True,
            "include_race_events": True,
            "include_testing_events": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "groups_processed": 2,
        "created": 6,
        "existing": 0,
        "season_contexts_created": 2,
        "race_event_contexts_created": 2,
        "testing_event_contexts_created": 2,
    }

    contexts = db_session.execute(
        select(BetContext).where(BetContext.season_id == season.id)
    ).scalars().all()
    assert len(contexts) == 6
    assert {context.group_id for context in contexts} == {first_group.id, second_group.id}


def test_generate_bet_contexts_endpoint_requires_group_header_for_non_admin(client, db_session) -> None:
    user = _create_local_user(
        db_session,
        username="owner_without_group_scope",
        password="secret123",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    season = Season(year=2032, is_active=False)
    db_session.add(season)
    db_session.flush()

    response = client.post(
        "/api/v1/admin/bet-contexts/generate",
        json={
            "season_id": season.id,
            "include_season": True,
            "include_race_events": False,
            "include_testing_events": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "admin.bet_context_generation_group_scope_required"


def test_generate_bet_contexts_endpoint_allows_owner_for_current_group(client, db_session) -> None:
    owner = _create_local_user(
        db_session,
        username="owner_generate_bet_contexts",
        password="secret123",
    )

    group = Group(
        name="Owner Managed Group",
        is_private=True,
        teams_enabled=False,
        max_team_size=None,
    )
    season = Season(year=2033, is_active=False)
    db_session.add_all([group, season])
    db_session.flush()

    _add_group_membership(
        db_session,
        user_id=owner.id,
        group_id=group.id,
        role=GroupRole.OWNER,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": owner.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/bet-contexts/generate",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "season_id": season.id,
            "include_season": True,
            "include_race_events": False,
            "include_testing_events": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "groups_processed": 1,
        "created": 1,
        "existing": 0,
        "season_contexts_created": 1,
        "race_event_contexts_created": 0,
        "testing_event_contexts_created": 0,
    }

    contexts = db_session.execute(
        select(BetContext).where(BetContext.group_id == group.id)
    ).scalars().all()
    assert len(contexts) == 1
    assert contexts[0].kind == BetContextKind.SEASON


def test_generate_bet_contexts_endpoint_allows_moderator_for_current_group(client, db_session) -> None:
    moderator = _create_local_user(
        db_session,
        username="moderator_generate_bet_contexts",
        password="secret123",
    )

    group = Group(
        name="Moderator Managed Group",
        is_private=True,
        teams_enabled=False,
        max_team_size=None,
    )
    season = Season(year=2035, is_active=False)
    db_session.add_all([group, season])
    db_session.flush()

    _add_group_membership(
        db_session,
        user_id=moderator.id,
        group_id=group.id,
        role=GroupRole.MODERATOR,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": moderator.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/bet-contexts/generate",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "season_id": season.id,
            "include_season": True,
            "include_race_events": False,
            "include_testing_events": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "groups_processed": 1,
        "created": 1,
        "existing": 0,
        "season_contexts_created": 1,
        "race_event_contexts_created": 0,
        "testing_event_contexts_created": 0,
    }


def test_generate_bet_contexts_endpoint_forbids_member_role_for_group_scope(client, db_session) -> None:
    member = _create_local_user(
        db_session,
        username="member_generate_bet_contexts",
        password="secret123",
    )

    group = Group(
        name="Member Managed Group",
        is_private=True,
        teams_enabled=False,
        max_team_size=None,
    )
    season = Season(year=2034, is_active=False)
    db_session.add_all([group, season])
    db_session.flush()

    _add_group_membership(
        db_session,
        user_id=member.id,
        group_id=group.id,
        role=GroupRole.MEMBER,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": member.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/bet-contexts/generate",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "season_id": season.id,
            "include_season": True,
            "include_race_events": False,
            "include_testing_events": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "admin.bet_context_generation_forbidden_group"


def test_create_country_endpoint_creates_country(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_create_country",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_create_country", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/countries",
        json={
            "iso2": "es",
            "name": "Spain",
            "flag_asset_url": "https://example.com/spain.png",
        },
    )

    assert response.status_code == 201
    assert response.json()["iso2"] == "ES"
    assert response.json()["name"] == "Spain"

    country = db_session.execute(
        select(Country).where(Country.iso2 == "ES")
    ).scalar_one()
    assert country.name == "Spain"
    assert country.flag_asset_url == "https://example.com/spain.png"

def test_create_country_endpoint_returns_conflict_for_duplicate_iso2(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_duplicate_country",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    db_session.add(
        Country(
            iso2="ES",
            name="Spain",
            flag_asset_url=None,
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_duplicate_country", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/countries",
        json={
            "iso2": "es",
            "name": "España",
            "flag_asset_url": None,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "admin.country_already_exists"





def test_create_circuit_endpoint_creates_circuit(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_create_circuit",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    country = Country(
        iso2="ES",
        name="Spain",
        flag_asset_url="https://example.com/flags/es.png",
    )
    db_session.add(country)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_create_circuit", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/circuits",
        json={
            "code": "barcelona",
            "name": "Circuit de Barcelona-Catalunya",
            "country_iso2": "es",
            "map_asset_url": "https://example.com/maps/barcelona.png",
            "image_asset_url": "https://example.com/images/barcelona.jpg",
        },
    )

    assert response.status_code == 201
    assert response.json()["code"] == "barcelona"
    assert response.json()["country_iso2"] == "ES"

    circuit = db_session.execute(
        select(Circuit).where(Circuit.code == "barcelona")
    ).scalar_one()
    assert circuit.name == "Circuit de Barcelona-Catalunya"


def test_create_circuit_endpoint_returns_conflict_for_duplicate_code(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_duplicate_circuit",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    country = Country(iso2="ES", name="Spain", flag_asset_url=None)
    db_session.add(country)
    db_session.flush()

    db_session.add(
        Circuit(
            code="barcelona",
            name="Circuit de Barcelona-Catalunya",
            country_id=country.id,
            map_asset_url=None,
            image_asset_url=None,
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_duplicate_circuit", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/circuits",
        json={
            "code": "barcelona",
            "name": "Otro nombre",
            "country_iso2": "es",
            "map_asset_url": None,
            "image_asset_url": None,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "admin.circuit_already_exists"



def test_create_circuit_endpoint_returns_not_found_for_missing_country(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_missing_country_circuit",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "admin_missing_country_circuit", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/v1/admin/circuits",
        json={
            "code": "barcelona",
            "name": "Circuit de Barcelona-Catalunya",
            "country_iso2": "zz",
            "map_asset_url": None,
            "image_asset_url": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "admin.country_not_found_for_circuit"
