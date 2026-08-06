from datetime import datetime
from typing import Protocol

from app.domain.auth.models import (
    AuthenticatedLoginUser,
    GoogleIdentity,
    PasswordResetTokenRecord,
)


class AuthRepository(Protocol):
    def get_by_id(self, user_id: int) -> AuthenticatedLoginUser | None:
        ...

    def get_by_username(self, username: str) -> AuthenticatedLoginUser | None:
        ...

    def get_by_google_sub(self, google_sub: str) -> AuthenticatedLoginUser | None:
        ...

    def create_local_user(self, *, username: str, password_hash: str) -> AuthenticatedLoginUser:
        ...

    def create_google_user(self, *, username: str, google_sub: str) -> AuthenticatedLoginUser:
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

class ResetTokenHasher(Protocol):
    def hash(self, raw_token: str) -> str:
        ...

class GoogleIdentityVerifier(Protocol):
    def verify(self, id_token: str) -> GoogleIdentity:
        ...
