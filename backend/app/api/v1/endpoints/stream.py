from fastapi import APIRouter

router = APIRouter()


@router.get("/{context_id}/stream")
def context_stream(context_id: int, session_id: int) -> dict:
    return {
        "context_id": context_id,
        "session_id": session_id,
        "events": ["bet_submitted", "bet_updated", "powerup_used", "results_published"],
        "note": "SSE placeholder endpoint. Replace with StreamingResponse(text/event-stream).",
    }
