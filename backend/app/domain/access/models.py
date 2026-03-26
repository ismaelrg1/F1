from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AuthenticatedUser:
    id: int
    role: str | None
    permission_codes: frozenset[str]


@dataclass(slots=True, frozen=True)
class AccessGroup:
    id: int
