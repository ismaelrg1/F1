from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from datetime import timedelta

import logging
import time


from app.adapters.security import PasslibPasswordHasher, Sha256ResetTokenHasher
from app.adapters.sqlalchemy import SqlAlchemyAuthRepository, SqlAlchemyPasswordResetTokenRepository
from app.api.deps import _translate_auth_error
from app.api.error_translators import get_preferred_locale

from app.core.config import settings
from app.db.session import get_db
from app.domain.auth import (
    AuthError,
    RequestPasswordReset,
    ResetPassword,
)
from app.models.auth import (
    PasswordForgotRequest,
    PasswordForgotResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)

logger = logging.getLogger(__name__)
PASSWORD_FORGOT_MIN_DURATION_SECONDS = 1.0

router = APIRouter()


def _sleep_remaining(started_at: float, *, minimum_duration: float) -> None:
    elapsed = time.monotonic() - started_at
    remaining = minimum_duration - elapsed
    if remaining > 0:
        time.sleep(remaining)



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
    use_case = RequestPasswordReset(
        auth_repository,
        token_repository,
        token_hasher,
        token_ttl=timedelta(minutes=settings.password_reset_token_expire_minutes),
        request_cooldown=timedelta(seconds=settings.password_reset_request_cooldown_seconds),
    )

    try:
        use_case.execute(data.username)
    except AuthError as exc:
        logger.warning(
            "Password reset request handled with internal auth error",
            extra={
                "error_type": type(exc).__name__,
                "error_context": getattr(exc, "context", {}),
                "username": data.username,
            },
        )

    _sleep_remaining(started_at, minimum_duration=PASSWORD_FORGOT_MIN_DURATION_SECONDS)


    return PasswordForgotResponse(
        msg="If the account exists, reset instructions have been sent"
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
