from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VisibleGroupResult:
    public_id: UUID
    name: str
    role: str | None
    teams_enabled: bool