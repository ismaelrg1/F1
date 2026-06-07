from uuid import UUID

from app.domain.management.scoring.errors import (
    ScoringBetContextNotFoundError,
    ScoringOfficialResultsRequiredError,
)
from app.domain.management.scoring.models import ScoringCalculationResult, ScoringScope
from app.domain.management.scoring.ports import ManagementScoringRepository


class CalculateRaceEventScoring:
    def __init__(self, repository: ManagementScoringRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
    ) -> ScoringCalculationResult:
        scope = self._repository.get_race_event_scope(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
        )
        if scope is None:
            raise ScoringBetContextNotFoundError()

        return _calculate(repository=self._repository, scope=scope)


class CalculateTestingEventScoring:
    def __init__(self, repository: ManagementScoringRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
    ) -> ScoringCalculationResult:
        scope = self._repository.get_testing_event_scope(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
        )
        if scope is None:
            raise ScoringBetContextNotFoundError()

        return _calculate(repository=self._repository, scope=scope)


class CalculateSeasonScoring:
    def __init__(self, repository: ManagementScoringRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> ScoringCalculationResult:
        scope = self._repository.get_season_scope(
            group_id=group_id,
            season_year=season_year,
        )
        if scope is None:
            raise ScoringBetContextNotFoundError()

        return _calculate(repository=self._repository, scope=scope)


def _calculate(
    *,
    repository: ManagementScoringRepository,
    scope: ScoringScope,
) -> ScoringCalculationResult:
    if not repository.official_results_exist(scope):
        raise ScoringOfficialResultsRequiredError()

    repository.delete_existing_scores(scope)
    result = repository.calculate_scores(scope)

    return result
