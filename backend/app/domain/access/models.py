from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class AuthenticatedUser:
    id: int
    public_id: UUID
    role: str | None
    permission_codes: frozenset[str]


@dataclass(slots=True, frozen=True)
class AccessGroup:
    id: int
    public_id: UUID
