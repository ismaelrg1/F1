from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from datetime import timedelta

import logging
import time

from app.adapters.google import GoogleIdTokenVerifier
from app.adapters.email import ResendEmailSender
from app.adapters.security import PasslibPasswordHasher, Sha256ResetTokenHasher
from app.adapters.sqlalchemy import SqlAlchemyAuthRepository, SqlAlchemyPasswordResetTokenRepository
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
from app.core.config import settings
from app.db.session import get_db
from app.domain.auth import (
    AuthError,
    LoginGoogleUser,
    LoginLocalUser,
    RegisterGoogleUser,
    RegisterLocalUser,
    RequestPasswordReset,
    ResetPassword,
)
from app.models.auth import (
    LoginLocalRequest,
    LoginGoogleRequest,
    LoginResponse,
    RegisterGoogleRequest,
    RegisterLocalRequest,
    RegisterResponse,
    UserSummary,
    PasswordForgotRequest,
    PasswordForgotResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)

logger = logging.getLogger(__name__)
PASSWORD_FORGOT_MIN_DURATION_SECONDS = 1.0

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


def _build_register_response(*, user, message: str) -> RegisterResponse:
    return RegisterResponse(
        msg=message,
        user=UserSummary(
            id=user.id,
            public_id=user.public_id,
            username=user.username,
            email=user.email,
        ),
    )

def _sleep_remaining(started_at: float, *, minimum_duration: float) -> None:
    elapsed = time.monotonic() - started_at
    remaining = minimum_duration - elapsed
    if remaining > 0:
        time.sleep(remaining)


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

    access_token = create_token(subject=str(user.id), token_type="access")
    refresh_token = create_token(subject=str(user.id), token_type="refresh")
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

    access_token = create_token(subject=str(user.id), token_type="access")
    refresh_token = create_token(subject=str(user.id), token_type="refresh")
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return _build_login_response(user=user, message="Logged in with Google")


@router.post("/register/local", response_model=RegisterResponse)
def register_local(
    data: RegisterLocalRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    repository = SqlAlchemyAuthRepository(db)
    password_hasher = PasslibPasswordHasher()
    use_case = RegisterLocalUser(repository, password_hasher)

    try:
        user = use_case.execute(username=data.username, email=data.email, password=data.password)
    except AuthError as exc:
        raise _translate_auth_error(exc, locale=locale) from exc

    return _build_register_response(user=user, message="Registered")


@router.post("/register/google", response_model=RegisterResponse)
def register_google(
    data: RegisterGoogleRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    repository = SqlAlchemyAuthRepository(db)
    verifier = GoogleIdTokenVerifier()
    use_case = RegisterGoogleUser(repository, verifier)

    try:
        user = use_case.execute(data.id_token)
    except AuthError as exc:
        raise _translate_auth_error(exc, locale=locale) from exc

    return _build_register_response(user=user, message="Registered with Google")

@router.post("/password/forgot", response_model=PasswordForgotResponse)
def password_forgot(
    data: PasswordForgotRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> PasswordForgotResponse:
    started_at = time.monotonic()
    
    auth_repository = SqlAlchemyAuthRepository(db)
    token_repository = SqlAlchemyPasswordResetTokenRepository(db)
    token_hasher = Sha256ResetTokenHasher()
    email_sender = ResendEmailSender()
    
    use_case = RequestPasswordReset(
        auth_repository,
        token_repository,
        token_hasher,
        email_sender,
        reset_base_url=f"{settings.frontend_base_url}/reset-password",
        token_ttl=timedelta(minutes=settings.password_reset_token_expire_minutes),
        request_cooldown=timedelta(seconds=settings.password_reset_request_cooldown_seconds),
    )

    try:
        use_case.execute(data.email)
    except AuthError as exc:
        logger.warning(
            "Password reset request handled with internal auth error",
            extra={
                "error_type": type(exc).__name__,
                "error_context": getattr(exc, "context", {}),
                "email": data.email,
            },
        )

    _sleep_remaining(started_at, minimum_duration=PASSWORD_FORGOT_MIN_DURATION_SECONDS)


    return PasswordForgotResponse(
        msg="If the account exists, a reset email has been sent"
    )


@router.post("/password/reset", response_model=PasswordResetResponse)
def password_reset(
    data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    auth_repository = SqlAlchemyAuthRepository(db)
    token_repository = SqlAlchemyPasswordResetTokenRepository(db)
    token_hasher = Sha256ResetTokenHasher()
    password_hasher = PasslibPasswordHasher()
    use_case = ResetPassword(
        auth_repository,
        token_repository,
        token_hasher,
        password_hasher,
    )

    try:
        use_case.execute(token=data.token, new_password=data.new_password)
    except AuthError as exc:
        raise _translate_auth_error(exc, locale=locale) from exc

    return PasswordResetResponse(msg="Password has been reset")


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
