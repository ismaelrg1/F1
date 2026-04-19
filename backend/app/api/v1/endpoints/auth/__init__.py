from fastapi import APIRouter

from . import password, registration, session
from .password import PASSWORD_FORGOT_MIN_DURATION_SECONDS, ResendEmailSender

router = APIRouter()
router.include_router(session.router)
router.include_router(registration.router)
router.include_router(password.router)

__all__ = [
    "router",
    "password",
    "registration",
    "session",
    "PASSWORD_FORGOT_MIN_DURATION_SECONDS",
    "ResendEmailSender",
]