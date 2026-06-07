from dataclasses import dataclass
from uuid import UUID

from app.db.enums import PowerUpTargetMode


@dataclass(frozen=True)
class BetPowerUpAvailability:
    code: str
    name: str
    target_mode: PowerUpTargetMode
    quantity: int
    is_enabled: bool
    is_restricted: bool
    already_used: bool


@dataclass(frozen=True)
class BetPowerUpsResult:
    powerups: list[BetPowerUpAvailability]
    race_event_public_id: UUID | None = None
    testing_event_public_id: UUID | None = None
    season_year: int | None = None