from dataclasses import dataclass
from datetime import datetime

from uuid import UUID


@dataclass(slots=True, frozen=True)
class AuthenticatedLoginUser:
    id: int
    public_id: UUID
    username: str
    email: str
    password_hash: str | None
    google_sub: str | None
    auth_provider: str | None

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
