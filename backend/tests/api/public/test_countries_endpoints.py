from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Permission, Role, User
from app.db.competition import Country
from app.db.enums import RoleName


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
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=[role],
    )
    db_session.add(user)
    db_session.flush()


def test_list_countries_requires_authentication(client) -> None:
    response = client.get("/api/v1/admin/countries")

    assert response.status_code == 401


def test_list_countries_returns_ordered_countries(client, db_session) -> None:
    _create_admin_user_with_permission(
        db_session,
        username="countries_reader",
        password="secret123",
        permission_code="COMPETITION_MANAGE",
    )

    db_session.add_all(
        [
            Country(iso2="IT", name="Italy", flag_asset_url=None),
            Country(iso2="ES", name="Spain", flag_asset_url="https://example.com/es.svg"),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "countries_reader", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/countries")

    assert response.status_code == 200
    payload = response.json()

    countries = db_session.execute(
        select(Country).order_by(Country.name.asc())
    ).scalars().all()

    assert [item["iso2"] for item in payload["items"]] == [country.iso2 for country in countries]
    assert [item["name"] for item in payload["items"]] == [country.name for country in countries]
    assert payload["items"][1]["flag_asset_url"] == "https://example.com/es.svg"
