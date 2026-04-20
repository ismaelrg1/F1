from pydantic import BaseModel, ConfigDict


class AdminBetContextGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season_id: int
    group_id: int | None = None
    include_season: bool = True
    include_race_events: bool = True
    include_testing_events: bool = True


class AdminBetContextGenerateResponse(BaseModel):
    groups_processed: int
    created: int
    existing: int
    season_contexts_created: int
    race_event_contexts_created: int
    testing_event_contexts_created: int