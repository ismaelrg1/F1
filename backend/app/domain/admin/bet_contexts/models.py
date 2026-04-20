from dataclasses import dataclass


@dataclass(frozen=True)
class AdminBetContextGenerationResult:
    groups_processed: int
    created: int
    existing: int
    season_contexts_created: int
    race_event_contexts_created: int
    testing_event_contexts_created: int