from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_ranking(season_year: int) -> dict:
    return {
        "year": season_year,
        "series": [{"username": "ana", "cumulative": [0, 5, 9, 12]}],
        "table": [{"rank": 1, "username": "ana", "points_total": 123.5}],
    }
