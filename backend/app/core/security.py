from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from fastapi import Response

from app.core.config import settings
from app.domain.auth import (
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
    MissingAccessTokenError,
    MissingRefreshSubjectError,
    MissingRefreshTokenError,
)

ACCESS_TOKEN_COOKIE_NAME = settings.jwt_access_cookie_name
REFRESH_TOKEN_COOKIE_NAME = settings.jwt_refresh_cookie_name
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_token(*, subject: str, token_type: Literal["access", "refresh"]) -> str:
    expires_in = (
        timedelta(minutes=settings.access_token_expire_minutes)
        if token_type == TOKEN_TYPE_ACCESS
        else timedelta(days=settings.refresh_token_expire_days)
    )
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_token(token: str, *, expected_type: Literal["access", "refresh"]) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        if expected_type == TOKEN_TYPE_ACCESS:
            raise InvalidAccessTokenError() from exc
        raise InvalidRefreshTokenError() from exc

    if payload.get("type") != expected_type:
        if expected_type == TOKEN_TYPE_ACCESS:
            raise InvalidAccessTokenError()
        raise InvalidRefreshTokenError()

    return payload


def get_access_token_subject(token: str | None) -> str:
    if not token:
        raise MissingAccessTokenError()

    payload = _decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
    subject = payload.get("sub")
    if not subject:
        raise InvalidAccessTokenError()
    return str(subject)


def get_refresh_token_subject(token: str | None) -> str:
    if not token:
        raise MissingRefreshTokenError()

    payload = _decode_token(token, expected_type=TOKEN_TYPE_REFRESH)
    subject = payload.get("sub")
    if not subject:
        raise MissingRefreshSubjectError()
    return str(subject)


def set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    cookie_secure = settings.jwt_cookie_secure
    if cookie_secure is None:
        cookie_secure = settings.app_env != "development"
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=settings.jwt_cookie_samesite,
        path="/",
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite=settings.jwt_cookie_samesite,
        path="/",
    )


def set_access_cookie(response: Response, *, access_token: str) -> None:
    cookie_secure = settings.jwt_cookie_secure
    if cookie_secure is None:
        cookie_secure = settings.app_env != "development"
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=settings.jwt_cookie_samesite,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path="/")
