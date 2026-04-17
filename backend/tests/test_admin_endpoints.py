from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.competition import Season, Country, Circuit
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


def test_create_season_endpoint_creates_season(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_create_season",
        email="admin_create_season@example.com",
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
        email="admin_duplicate_season@example.com",
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
        email="admin_active_season@example.com",
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
        email="admin_list_seasons@example.com",
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
        email="admin_patch_season@example.com",
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
        email="admin_patch_missing_season@example.com",
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


def test_create_country_endpoint_creates_country(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="admin_create_country",
        email="admin_create_country@example.com",
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
        email="admin_duplicate_country@example.com",
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
        email="admin_create_circuit@example.com",
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
        email="admin_duplicate_circuit@example.com",
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
        email="admin_missing_country_circuit@example.com",
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
