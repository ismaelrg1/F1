from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BetCreate(BaseModel):
    context_id: int
    event_session_id: int


class BetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bet_context_id: int
    event_session_id: int
    user_id: int
    last_modified_at: datetime | None = None
