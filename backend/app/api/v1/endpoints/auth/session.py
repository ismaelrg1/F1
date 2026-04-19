from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

import logging

from app.adapters.google import GoogleIdTokenVerifier
from app.adapters.security import PasslibPasswordHasher
from app.adapters.sqlalchemy import SqlAlchemyAuthRepository
from app.api.deps import _translate_auth_error
from app.api.error_translators import get_preferred_locale
from app.core.security import (
    REFRESH_TOKEN_COOKIE_NAME,
    clear_auth_cookies,
    create_token,
    get_refresh_token_subject,
    set_access_cookie,
    set_auth_cookies,
)
from app.db.session import get_db
from app.domain.auth import (
    AuthError,
    LoginGoogleUser,
    LoginLocalUser,
)
from app.models.auth import (
    LoginLocalRequest,
    LoginGoogleRequest,
    LoginResponse,
    UserSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter()

def _build_login_response(*, user, message: str) -> LoginResponse:
    return LoginResponse(
        msg=message,
        user=UserSummary(
            id=user.id,
            public_id=user.public_id,
            username=user.username,
            email=user.email,
        ),
    )


@router.post("/login", response_model=LoginResponse)
@router.post("/login/local", response_model=LoginResponse)
def login_local(
    data: LoginLocalRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    repository = SqlAlchemyAuthRepository(db)
    password_hasher = PasslibPasswordHasher()
    use_case = LoginLocalUser(repository, password_hasher)

    try:
        user = use_case.execute(data.username, data.password)
    except AuthError as exc:
        raise _translate_auth_error(exc, locale=locale) from exc

    access_token = create_token(subject=str(user.public_id), token_type="access")
    refresh_token = create_token(subject=str(user.public_id), token_type="refresh")
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return _build_login_response(user=user, message="Logged in")


@router.post("/login/google", response_model=LoginResponse)
def login_google(
    data: LoginGoogleRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    repository = SqlAlchemyAuthRepository(db)
    verifier = GoogleIdTokenVerifier()
    use_case = LoginGoogleUser(repository, verifier)

    try:
        user = use_case.execute(data.id_token)
    except AuthError as exc:
        raise _translate_auth_error(exc, locale=locale) from exc

    access_token = create_token(subject=str(user.public_id), token_type="access")
    refresh_token = create_token(subject=str(user.public_id), token_type="refresh")
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return _build_login_response(user=user, message="Logged in with Google")


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
) -> dict[str, str]:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    try:
        token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME) if request else None
        subject = get_refresh_token_subject(token)
    except AuthError as exc:
        raise _translate_auth_error(exc, locale=locale) from exc

    access_token = create_token(subject=subject, token_type="access")
    set_access_cookie(response, access_token=access_token)
    return {"msg": "Token refreshed"}


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    clear_auth_cookies(response)
    return {"msg": "Logged out"}
