from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import User
from app.db.competition import Country


def _create_user(
    db_session,
    *,
    username: str,
    email: str,
    password: str,
) -> None:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
    )
    db_session.add(user)
    db_session.flush()


def test_list_countries_requires_authentication(client) -> None:
    response = client.get("/api/v1/countries")

    assert response.status_code == 401


def test_list_countries_returns_ordered_countries(client, db_session) -> None:
    _create_user(
        db_session,
        username="countries_reader",
        email="countries_reader@example.com",
        password="secret123",
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

    response = client.get("/api/v1/countries")

    assert response.status_code == 200
    payload = response.json()

    countries = db_session.execute(
        select(Country).order_by(Country.name.asc())
    ).scalars().all()

    assert [item["iso2"] for item in payload["items"]] == [country.iso2 for country in countries]
    assert [item["name"] for item in payload["items"]] == [country.name for country in countries]
    assert payload["items"][1]["flag_asset_url"] == "https://example.com/es.svg"
