from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.auth.models import AuthenticatedLoginUser


@dataclass(slots=True, frozen=True)
class GoogleIdentity:
    sub: str
    email: str
    email_verified: bool

@dataclass(frozen=True)
class PasswordResetTokenRecord:
    user_id: int
    token_hash: str
    expires_at: datetime
    used_at: datetime | None
    invalidated_at: datetime | None
    created_at: datetime


class AuthRepository(Protocol):
    def get_by_id(self, user_id: int) -> AuthenticatedLoginUser | None:
        ...

    def get_by_username(self, username: str) -> AuthenticatedLoginUser | None:
        ...

    def get_by_email(self, email: str) -> AuthenticatedLoginUser | None:
        ...

    def get_by_google_sub(self, google_sub: str) -> AuthenticatedLoginUser | None:
        ...

    def create_local_user(self, *, username: str, email: str, password_hash: str) -> AuthenticatedLoginUser:
        ...

    def create_google_user(self, *, username: str, email: str, google_sub: str) -> AuthenticatedLoginUser:
        ...

    def update_password(self, *, user_id: int, password_hash: str) -> None:
        ...

class PasswordHasher(Protocol):
    def verify(self, plain_password: str, password_hash: str) -> bool:
        ...

    def hash(self, plain_password: str) -> str:
        ...

class PasswordResetTokenRepository(Protocol):
    def get_active_for_user(self, user_id: int) -> PasswordResetTokenRecord | None:
        ...

    def invalidate_active_for_user(self, user_id: int, *, invalidated_at: datetime) -> None:
        ...

    def create_token(
            self,
            *,
            user_id: int,
            token_hash: str,
            expires_at: datetime,
    ) -> None:
        ...

    def get_by_token_hash(self, token_hash: str) -> PasswordResetTokenRecord | None:
        ...

    def mark_as_used(self, token_hash: str, *, used_at: datetime) -> None:
        ...

class EmailSender(Protocol):
    def send_password_reset_email(self, *, to_email: str, reset_url: str) -> None:
        ...

class ResetTokenHasher(Protocol):
    def hash(self, raw_token: str) -> str:
        ...

class GoogleIdentityVerifier(Protocol):
    def verify(self, id_token: str) -> GoogleIdentity:
        ...
