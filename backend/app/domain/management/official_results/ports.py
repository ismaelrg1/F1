from typing import Protocol
from uuid import UUID

from app.db.scoring.official_result import SourceType
from app.domain.management.official_results.models import (
    OfficialResult,
    OfficialResultInput,
)


class OfficialResultRepository(Protocol):
    def get_bet_context_scope(
        self,
        *,
        bet_context_public_id: UUID,
    ) -> tuple[int, UUID]:
        ...

    def get_event_session_scope(
        self,
        *,
        bet_context_id: int,
        event_session_public_id: UUID,
    ) -> tuple[int, UUID] | None:
        ...

    def get_testing_event_session_scope(
        self,
        *,
        bet_context_id: int,
        testing_event_session_public_id: UUID,
    ) -> tuple[int, UUID] | None:
        ...

    def get_bet_score_ids_by_codes(
        self,
        *,
        codes: set[str],
    ) -> dict[str, int]:
        ...

    def official_results_exist_for_scope(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        bet_score_ids: set[int],
    ) -> bool:
        ...

    def official_results_missing_for_scope(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        bet_score_ids: set[int],
    ) -> bool:
        ...

    def create_official_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        source: SourceType,
        results: list[OfficialResultInput],
        score_ids_by_code: dict[str, int],
    ) -> list[OfficialResult]:
        ...

    def update_official_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        source: SourceType,
        results: list[OfficialResultInput],
        score_ids_by_code: dict[str, int],
    ) -> list[OfficialResult]:
        ...

    def get_bet_context_group_id(
        self,
        *,
        bet_context_public_id: UUID,
    ) -> int | None:
        ...

    def get_group_role(
        self,
        *,
        user_id: int,
        group_id: int,
    ) -> str | None:
        ...