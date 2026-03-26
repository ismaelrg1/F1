from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_seasons() -> dict:
    return {"items": [{"id": 1, "year": 2026, "title": "Season 2026", "is_active": True}]}


@router.get("/active")
def active_season() -> dict:
    return {"item": {"id": 1, "year": 2026, "title": "Season 2026", "is_active": True}}


@router.get("/{season_id}")
def get_season(season_id: int) -> dict:
    return {"item": {"id": season_id, "year": 2026, "title": "Season 2026", "is_active": True}}


@router.get("/{season_id}/roster")
def season_roster(season_id: int) -> dict:
    return {
        "season_id": season_id,
        "drivers": [{"code": "ALO", "name": "Fernando Alonso"}],
        "teams": [{"code": "FER", "name": "Ferrari"}],
        "engines": [{"code": "HONDA", "name": "Honda"}],
    }
