from app.adapters.security import PasslibPasswordHasher
from app.db.auth import User
from app.db.competition import Season


def _create_user(
    db_session,
    *,
    username: str,
    password: str,
) -> None:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
    )
    db_session.add(user)
    db_session.flush()


def test_get_seasons_requires_authentication(client) -> None:
    response = client.get("/api/v1/seasons")

    assert response.status_code == 401


def test_get_seasons_returns_ordered_years_for_logged_user(client, db_session) -> None:
    _create_user(
        db_session,
        username="season_reader",
        password="secret123",
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
        json={"username": "season_reader", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/seasons")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"year": 2026},
            {"year": 2025},
            {"year": 2024},
        ]
    }
