from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ScoringScope:
    group_id: int
    season_id: int
    bet_context_id: int
    race_event_id: int | None = None
    testing_event_id: int | None = None
    event_session_ids: tuple[int, ...] = ()
    testing_event_session_ids: tuple[int, ...] = ()

    @property
    def is_race_event(self) -> bool:
        return self.race_event_id is not None

    @property
    def is_testing_event(self) -> bool:
        return self.testing_event_id is not None

    @property
    def is_season(self) -> bool:
        return self.race_event_id is None and self.testing_event_id is None


@dataclass
class ScoringCalculationResult:
    calculated: bool
    calculated_users: int
    score_components_count: int
    score_session_components_count: int
    computed_at: datetime