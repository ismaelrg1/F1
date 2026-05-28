from typing import Protocol
from uuid import UUID

from app.domain.management.scoring.models import (
    ScoringCalculationResult,
    ScoringScope,
)


class ManagementScoringRepository(Protocol):
    def get_race_event_scope(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
    ) -> ScoringScope | None:
        ...

    def get_testing_event_scope(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
    ) -> ScoringScope | None:
        ...

    def get_season_scope(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> ScoringScope | None:
        ...

    def official_results_exist(self, scope: ScoringScope) -> bool:
        ...

    def delete_existing_scores(self, scope: ScoringScope) -> None:
        ...

    def calculate_scores(self, scope: ScoringScope) -> ScoringCalculationResult:
        ...

    def recalculate_season_aggregates(self, scope: ScoringScope) -> None:
        ...