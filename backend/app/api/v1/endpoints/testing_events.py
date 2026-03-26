from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_testing_events(season_id: int | None = None) -> dict:
    return {"items": [{"id": 3, "season_id": season_id or 1, "name": "Pre-Season Testing"}]}


@router.get("/{testing_event_id}")
def get_testing_event(testing_event_id: int) -> dict:
    return {"item": {"id": testing_event_id, "season_id": 1, "name": "Pre-Season Testing"}}
