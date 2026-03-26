from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class UsePowerupBody(BaseModel):
    bet_context_id: int
    event_session_id: int
    powerup_code: str
    targets: list[dict]


@router.get("")
def list_powerups() -> dict:
    return {"items": [{"id": 1, "code": "HALF", "name": "/2", "target_mode": "SINGLE", "is_enabled": True}]}


@router.get("/assignments/mine")
def my_assignments(season_id: int) -> dict:
    return {"season_id": season_id, "items": [{"powerup_code": "HALF", "quantity": 2}]}


@router.post("/use")
def use_powerup(_: UsePowerupBody) -> dict:
    return {"ok": True}
