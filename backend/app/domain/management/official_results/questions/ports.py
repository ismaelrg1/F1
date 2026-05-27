from typing import Protocol

from app.domain.management.official_results.questions.models import (
    ExistingOfficialResult,
    OfficialResultScopeKey,
)


class OfficialResultQuestionsRepository(Protocol):
    def list_official_results_for_context(
        self,
        *,
        bet_context_id: int,
    ) -> list[ExistingOfficialResult]:
        ...

    def list_result_publications_for_context(
        self,
        *,
        bet_context_id: int,
    ) -> set[OfficialResultScopeKey]:
        ...