from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
from sqlalchemy import select

from app.adapters.google import GoogleIdTokenVerifier
from app.adapters.security import PasslibPasswordHasher, Sha256ResetTokenHasher
from app.core.config import settings
from app.db.auth import PasswordResetToken
from app.db.auth import User


def _unique_user_data(prefix: str) -> tuple[str, str]:
    suffix = uuid4().hex[:10]
    username = f"{prefix}_{suffix}"
    email = f"{prefix}_{suffix}@example.com"
    return username, email


def _create_local_user(db_session, *, username: str, email: str, password: str) -> None:
    hasher = PasslibPasswordHasher()
    db_session.add(
        User(
            username=username,
            email=email,
            password_hash=hasher.hash(password),
            auth_provider="LOCAL",
        )
    )
    db_session.flush()


def _create_google_user(db_session, *, username: str, email: str, google_sub: str) -> None:
    db_session.add(
        User(
            username=username,
            email=email,
            google_sub=google_sub,
            auth_provider="GOOGLE",
        )
    )
    db_session.flush()


def test_register_local_endpoint_persists_user_in_db(client, db_session) -> None:
    username, _email = _unique_user_data("register_local")

    response = client.post(
        "/api/v1/auth/register/local",
        json={
            "username": username,
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["username"] == username
    assert "email" not in response.json()["user"]

    user = db_session.execute(select(User).where(User.username == username)).scalar_one()
    assert user.username == username
    assert user.auth_provider == "LOCAL"
    assert user.password_hash is not None
    assert user.password_hash != "secret123"


def test_login_local_endpoint_sets_jwt_cookies(client, db_session) -> None:
    username, email = _unique_user_data("login_local")

    _create_local_user(db_session, username=username, email=email, password="secret123")

    response = client.post(
        "/api/v1/auth/login/local",
        json={"username": username, "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.cookies.get("access_token_cookie") is not None
    assert response.cookies.get("refresh_token_cookie") is not None


def test_login_local_endpoint_sets_public_id_as_jwt_subject(client, db_session) -> None:
    username, email = _unique_user_data("login_subject")

    _create_local_user(db_session, username=username, email=email, password="secret123")
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()

    response = client.post(
        "/api/v1/auth/login/local",
        json={"username": username, "password": "secret123"},
    )

    assert response.status_code == 200

    access_token = response.cookies.get("access_token_cookie")
    assert access_token is not None

    payload = jwt.decode(
        access_token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == str(user.public_id)


def test_refresh_endpoint_uses_refresh_cookie_after_login(client, db_session) -> None:
    username, email = _unique_user_data("refresh_local")

    _create_local_user(db_session, username=username, email=email, password="secret123")

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    refresh_response = client.post("/api/v1/auth/refresh")

    assert refresh_response.status_code == 200
    assert refresh_response.json()["msg"] == "Token refreshed"
    assert refresh_response.cookies.get("access_token_cookie") is not None


def test_register_google_endpoint_persists_google_user(client, db_session, monkeypatch) -> None:
    username, email = _unique_user_data("register_google")
    google_sub = f"google-{uuid4().hex}"

    def fake_verify(self, _raw_id_token: str):
        return SimpleNamespace(sub=google_sub, email=email, email_verified=True)

    monkeypatch.setattr(GoogleIdTokenVerifier, "verify", fake_verify)

    response = client.post(
        "/api/v1/auth/register/google",
        json={"id_token": "fake-google-token"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["username"] == username
    assert "email" not in response.json()["user"]

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    assert user.auth_provider == "GOOGLE"
    assert user.google_sub == google_sub
    assert user.password_hash is None


def test_login_google_endpoint_sets_jwt_cookies(client, db_session, monkeypatch) -> None:
    username, email = _unique_user_data("login_google")
    google_sub = f"google-{uuid4().hex}"

    def fake_verify(self, _raw_id_token: str):
        return SimpleNamespace(sub=google_sub, email=email, email_verified=True)

    monkeypatch.setattr(GoogleIdTokenVerifier, "verify", fake_verify)

    _create_google_user(db_session, username=username, email=email, google_sub=google_sub)

    response = client.post(
        "/api/v1/auth/login/google",
        json={"id_token": "fake-google-token"},
    )

    assert response.status_code == 200
    assert response.cookies.get("access_token_cookie") is not None
    assert response.cookies.get("refresh_token_cookie") is not None


def test_password_reset_endpoint_updates_local_user_password(client, db_session) -> None:
    username, email = _unique_user_data("reset_password")
    raw_token = "reset-token-123"
    token_hash = Sha256ResetTokenHasher().hash(raw_token)

    _create_local_user(db_session, username=username, email=email, password="oldsecret")

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    db_session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
    )
    db_session.flush()

    response = client.post(
        "/api/v1/auth/password/reset",
        json={"token": raw_token, "new_password": "newsecret123"},
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "Password has been reset"

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    assert PasslibPasswordHasher().verify("newsecret123", user.password_hash)
    token = db_session.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)).scalar_one()
    assert token.used_at is not None


def test_password_reset_endpoint_returns_same_error_for_unknown_token(client) -> None:
    response = client.post(
        "/api/v1/auth/password/reset",
        json={"token": "missing-token", "new_password": "newsecret123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "auth.invalid_password_reset_token"


def test_password_reset_endpoint_returns_same_error_for_used_token(client, db_session) -> None:
    username, email = _unique_user_data("reset_used")
    raw_token = "used-token-123"
    token_hash = Sha256ResetTokenHasher().hash(raw_token)

    _create_local_user(db_session, username=username, email=email, password="oldsecret")

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    db_session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            used_at=datetime.now(UTC),
        )
    )
    db_session.flush()

    response = client.post(
        "/api/v1/auth/password/reset",
        json={"token": raw_token, "new_password": "newsecret123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "auth.invalid_password_reset_token"

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    assert PasslibPasswordHasher().verify("oldsecret", user.password_hash)


def test_password_reset_endpoint_returns_same_error_for_expired_token(client, db_session) -> None:
    username, email = _unique_user_data("reset_expired")
    raw_token = "expired-token-123"
    token_hash = Sha256ResetTokenHasher().hash(raw_token)

    _create_local_user(db_session, username=username, email=email, password="oldsecret")

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    db_session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    db_session.flush()

    response = client.post(
        "/api/v1/auth/password/reset",
        json={"token": raw_token, "new_password": "newsecret123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "auth.invalid_password_reset_token"

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    assert PasslibPasswordHasher().verify("oldsecret", user.password_hash)


def test_password_reset_endpoint_returns_same_error_for_invalidated_token(client, db_session) -> None:
    username, email = _unique_user_data("reset_invalidated")
    raw_token = "invalidated-token-123"
    token_hash = Sha256ResetTokenHasher().hash(raw_token)

    _create_local_user(db_session, username=username, email=email, password="oldsecret")

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    db_session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            invalidated_at=datetime.now(UTC),
        )
    )
    db_session.flush()

    response = client.post(
        "/api/v1/auth/password/reset",
        json={"token": raw_token, "new_password": "newsecret123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "auth.invalid_password_reset_token"

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    assert PasslibPasswordHasher().verify("oldsecret", user.password_hash)


def test_password_forgot_endpoint_creates_reset_token_for_local_user(client, db_session, monkeypatch) -> None:
    username, email = _unique_user_data("forgot_local")

    _create_local_user(db_session, username=username, email=email, password="oldsecret")
    monkeypatch.setattr("app.api.v1.endpoints.auth.password.PASSWORD_FORGOT_MIN_DURATION_SECONDS", 0.0)
    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.ResendEmailSender.send_password_reset_email",
        lambda self, *, to_email, reset_url: None,
    )

    response = client.post(
        "/api/v1/auth/password/forgot",
        json={"username": username},
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "If the account exists, reset instructions have been sent"

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    token = db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    ).scalar_one()
    assert token.used_at is None
    assert token.invalidated_at is None


def test_password_forgot_endpoint_returns_neutral_success_for_unknown_user(client, monkeypatch) -> None:
    username, _email = _unique_user_data("forgot_unknown")
    monkeypatch.setattr("app.api.v1.endpoints.auth.password.PASSWORD_FORGOT_MIN_DURATION_SECONDS", 0.0)

    response = client.post(
        "/api/v1/auth/password/forgot",
        json={"username": username},
    )

    assert response.status_code == 200
    assert response.json()["msg"] == "If the account exists, reset instructions have been sent"


def test_password_forgot_endpoint_logs_internal_error_for_google_user(client, db_session, monkeypatch, caplog) -> None:
    username, email = _unique_user_data("forgot_google")

    _create_google_user(db_session, username=username, email=email, google_sub=f"google-{uuid4().hex}")
    monkeypatch.setattr("app.api.v1.endpoints.auth.password.PASSWORD_FORGOT_MIN_DURATION_SECONDS", 0.0)

    with caplog.at_level("WARNING", logger="app.api.v1.endpoints.auth"):
        response = client.post(
            "/api/v1/auth/password/forgot",
            json={"username": username},
        )

    assert response.status_code == 200
    assert response.json()["msg"] == "If the account exists, reset instructions have been sent"
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.msg == "Password reset request handled with internal auth error"
    assert record.error_type == "PasswordResetNotAvailableError"
    assert record.error_context == {"provider": "GOOGLE"}
    assert record.username == username


def test_password_forgot_endpoint_logs_internal_error_for_cooldown(client, db_session, monkeypatch, caplog) -> None:
    username, email = _unique_user_data("forgot_cooldown")

    _create_local_user(db_session, username=username, email=email, password="oldsecret")
    monkeypatch.setattr("app.api.v1.endpoints.auth.password.PASSWORD_FORGOT_MIN_DURATION_SECONDS", 0.0)

    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    db_session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=Sha256ResetTokenHasher().hash("active-token"),
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
    )
    db_session.flush()

    with caplog.at_level("WARNING", logger="app.api.v1.endpoints.auth"):
        response = client.post(
            "/api/v1/auth/password/forgot",
            json={"username": username},
        )

    assert response.status_code == 200
    assert response.json()["msg"] == "If the account exists, reset instructions have been sent"
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.msg == "Password reset request handled with internal auth error"
    assert record.error_type == "PasswordResetTooManyRequestsError"
    assert record.error_context == {"cooldown_seconds": 60}
    assert record.username == username
