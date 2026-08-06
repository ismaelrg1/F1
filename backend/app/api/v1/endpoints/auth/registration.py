from hashlib import sha256

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import logging

from app.adapters.google import GoogleIdTokenVerifier
from app.adapters.security import PasslibPasswordHasher
from app.adapters.sqlalchemy import SqlAlchemyAuthRepository
from app.api.deps import _translate_auth_error
from app.api.error_translators import get_preferred_locale


from app.db.session import get_db
from app.domain.auth import (
    AuthError,
    RegisterGoogleUser,
    RegisterLocalUser,
)
from app.models.auth import (
    RegisterGoogleRequest,
    RegisterLocalRequest,
    RegisterResponse,
    UserSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _internal_email_for_username(username: str) -> str:
    digest = sha256(username.encode("utf-8")).hexdigest()[:16]
    return f"{digest}@local.futuref1.invalid"


def _build_register_response(*, user, message: str) -> RegisterResponse:
    return RegisterResponse(
        msg=message,
        user=UserSummary(
            id=user.id,
            public_id=user.public_id,
            username=user.username,
        ),
    )


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
        user = use_case.execute(
            username=data.username,
            email=_internal_email_for_username(data.username),
            password=data.password,
        )
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
