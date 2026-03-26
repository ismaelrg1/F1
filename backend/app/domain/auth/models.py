from dataclasses import dataclass
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
