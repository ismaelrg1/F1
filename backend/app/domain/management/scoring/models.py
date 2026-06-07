from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


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

@dataclass
class ScoringPickResult:
    user_id: int
    bet_id: int
    bet_pick_id: int
    bet_score_id: int
    bet_score_code: str
    event_session_id: int | None
    testing_event_session_id: int | None
    points: Decimal
    hit: bool
    component_type: str
    evaluator_key: str
    details: dict[str, Any]


@dataclass
class UserScoreState:
    user_id: int
    base_points: Decimal = Decimal("0")
    extra_points: Decimal = Decimal("0")
    powerup_points: Decimal = Decimal("0")
    penalty_points: Decimal = Decimal("0")
    pick_results: list[ScoringPickResult] = field(default_factory=list)

    @property
    def total_points(self) -> Decimal:
        return self.base_points + self.extra_points + self.powerup_points - self.penalty_points
    

@dataclass(frozen=True)
class PowerUpEvaluationContext:
    powerup_code: str
    actor_user_id: int
    target_user_ids: tuple[int, ...]
    event_session_id: int | None
    testing_event_session_id: int | None
    base_points_by_user: dict[int, Decimal]
    rule_json: dict[str, Any]


@dataclass(frozen=True)
class PowerUpEffect:
    target_user_id: int
    component_type: str
    code: str
    points: Decimal
    details: dict[str, Any]