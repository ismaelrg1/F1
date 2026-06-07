from typing import Protocol
from uuid import UUID

from app.domain.management.result_publications.models import ResultPublicationResult


class ResultPublicationRepository(Protocol):
    def get_race_bet_context_id(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
    ) -> int | None:
        ...

    def get_testing_bet_context_id(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
    ) -> int | None:
        ...

    def get_season_bet_context_id(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> int | None:
        ...

    def get_event_session_id(
        self,
        *,
        bet_context_id: int,
        event_session_public_id: UUID,
    ) -> int | None:
        ...

    def get_testing_event_session_id(
        self,
        *,
        bet_context_id: int,
        testing_event_session_public_id: UUID,
    ) -> int | None:
        ...

    def official_results_exist(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        ...

    def publication_exists(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        ...

    def create_publication(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        published_by_user_id: int,
        note: str | None,
    ) -> ResultPublicationResult:
        ...

    def delete_publication(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> None:
        ...

    def has_calculated_scores(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        ...

    def recalculate_season_aggregates_for_bet_context(
        self,
        *,
        bet_context_id: int,
    ) -> None:
        ...
    