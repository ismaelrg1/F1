from dataclasses import dataclass
from uuid import UUID

from app.db.enums import PowerUpTargetMode


@dataclass(frozen=True)
class BetPowerUpTargetUserDefinition:
    user_id: int
    user_public_id: UUID
    username: str


@dataclass(frozen=True)
class BetPowerUpTargetTeamDefinition:
    team_id: int
    team_public_id: UUID
    name: str


@dataclass(frozen=True)
class BetPowerUpTargetOption:
    target_type: str
    target_user_public_id: UUID | None = None
    target_team_public_id: UUID | None = None
    target_group_public_id: UUID | None = None
    label: str = ""
    is_available: bool = True
    unavailable_reason: str | None = None


@dataclass(frozen=True)
class BetPowerUpAvailability:
    powerup_id: int
    code: str
    name: str
    target_mode: PowerUpTargetMode
    quantity: int
    is_enabled: bool
    is_restricted: bool
    already_used: bool
    target_options: list[BetPowerUpTargetOption]


@dataclass(frozen=True)
class BetPowerUpsResult:
    powerups: list[BetPowerUpAvailability]
    race_event_public_id: UUID | None = None
    testing_event_public_id: UUID | None = None
    season_year: int | None = None