from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScoringCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    calculated: bool
    calculated_users: int
    score_components_count: int
    score_session_components_count: int
    computed_at: datetime