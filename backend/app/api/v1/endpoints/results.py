from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
editor_router = APIRouter(prefix="/editor")


class ResultsBody(BaseModel):
    context_id: int
    event_session_id: int
    items: list[dict]


class PublishBody(BaseModel):
    context_id: int
    event_session_id: int


@router.get("")
def list_results(context_id: int, session_id: int) -> dict:
    return {"context_id": context_id, "session_id": session_id, "results_published": False, "items": []}


@editor_router.post("/results", status_code=201)
def upsert_results(_: ResultsBody) -> dict:
    return {"ok": True}


@editor_router.post("/results/publish")
def publish_results(_: PublishBody) -> dict:
    return {"ok": True, "results_published": True, "published_at": "2026-05-24T16:00:00Z"}


@editor_router.post("/contexts/{context_id}/recalculate")
def recalculate_context(context_id: int, session_id: int) -> dict:
    return {"ok": True, "context_id": context_id, "session_id": session_id}
