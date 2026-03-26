from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_race_events(season_id: int | None = None) -> dict:
    return {
        "items": [
            {
                "id": 10,
                "season_id": season_id or 1,
                "name": "Monaco GP",
                "event_start": "2026-05-22T00:00:00Z",
                "event_end": "2026-05-24T00:00:00Z",
                "circuit_id": 7,
                "country_code": "MC",
            }
        ]
    }


@router.get("/{race_event_id}")
def get_race_event(race_event_id: int) -> dict:
    return {"item": {"id": race_event_id, "season_id": 1, "name": "Monaco GP"}}


@router.get("/{race_event_id}/sessions")
def race_event_sessions(race_event_id: int) -> dict:
    return {
        "items": [
            {
                "id": 55,
                "race_event_id": race_event_id,
                "session_type": "RACE",
                "start_datetime": "2026-05-24T14:00:00Z",
                "lock_cutoff": "2026-05-24T13:55:00Z",
                "results_published": False,
                "results_published_at": None,
            }
        ]
    }
