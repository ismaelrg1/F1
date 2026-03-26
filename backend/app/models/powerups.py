from pydantic import BaseModel


class PowerUpRead(BaseModel):
    id: int
    code: str
    name: str
    target_mode: str
    is_enabled: bool


class PowerUpAssignmentRead(BaseModel):
    powerup_code: str
    quantity: int


class UsePowerupRequest(BaseModel):
    bet_context_id: int
    event_session_id: int
    powerup_code: str
    targets: list[dict]
