from pydantic import BaseModel


class ResultsQuery(BaseModel):
    context_id: int
    session_id: int


class ResultsUpsertRequest(BaseModel):
    context_id: int
    event_session_id: int
    items: list[dict]


class PublishResultsRequest(BaseModel):
    context_id: int
    event_session_id: int
