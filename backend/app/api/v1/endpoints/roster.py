from fastapi import APIRouter

router = APIRouter()


@router.get("/{season_id}/roster")
def roster(season_id: int) -> dict:
    return {
        "season_id": season_id,
        "drivers": [{"code": "ALO", "name": "Fernando Alonso"}],
        "teams": [{"code": "FER", "name": "Ferrari"}],
        "engines": [{"code": "HONDA", "name": "Honda"}],
    }
