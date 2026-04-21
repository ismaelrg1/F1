from typing import Protocol
from datetime import datetime
from uuid import UUID

from app.domain.bets.models import (
    # Results
    BetResultEntry,
    BetResultsVisibility,
    BetOfficialResult,

    # Shared
    BetContextDefinition,
    BetRaceEvent,

)


class BetResultsRepository(Protocol):
    def get_race_event_by_public_id(self, public_id: UUID) -> BetRaceEvent | None:
        ...


    def get_gp_bet_context(self, *, group_id: int, race_event_id: int) -> BetContextDefinition | None:
        ...


    def get_race_event_visibility(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        now: datetime,
    ) -> BetResultsVisibility:
        ...


    def viewer_has_submitted_scope(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> bool:
        ...


    def list_official_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> list[BetOfficialResult]:
        ...


    def list_group_submitted_bet_entries(
        self,
        *,
        group_id: int,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> list[BetResultEntry]:
        ...