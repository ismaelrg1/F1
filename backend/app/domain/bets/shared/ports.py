from typing import Protocol
from uuid import UUID
from datetime import datetime

from app.domain.bets.models import (
    BetContextDefinition,
    BetRaceEvent,
    BetSeason,
    BetTemplateDefinition,
    BetTestingEvent,
    UserBetDefinition,
    BetAnswerInput,
    BetEditPermissionDefinition,
)


class BetQuestionsRepository(Protocol):
    def get_race_event_by_public_id(self, public_id: UUID) -> BetRaceEvent | None:
        ...

    def get_testing_event_by_public_id(self, public_id: UUID) -> BetTestingEvent | None:
        ...

    def get_season_by_year(self, year: int) -> BetSeason | None:
        ...

    def get_gp_bet_context(self, *, group_id: int, race_event_id: int) -> BetContextDefinition | None:
        ...

    def get_pretesting_bet_context(self, *, group_id: int, testing_event_id: int) -> BetContextDefinition | None:
        ...

    def get_season_bet_context(self, *, group_id: int, season_id: int) -> BetContextDefinition | None:
        ...

    def list_gp_templates_for_season(self, *, season_id: int) -> list[BetTemplateDefinition]:
        ...

    def list_pretesting_templates_for_season(self, *, season_id: int) -> list[BetTemplateDefinition]:
        ...

    def list_season_templates_for_season(self, *, season_id: int) -> list[BetTemplateDefinition]:
        ...

    def list_user_bets_for_context(self, *, user_id: int, bet_context_id: int) -> list[UserBetDefinition]:
        ...

    def get_bet_score_ids_by_codes(self, *, codes: set[str]) -> dict[str, int]:
        ...

    def upsert_user_bet_draft(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        answers: list[BetAnswerInput],
        modified_at: datetime,
    ) -> None:
        ...

    def list_active_edit_permissions_for_scope(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        now: datetime,
    ) -> list[BetEditPermissionDefinition]:
        ...

    def upsert_user_bet_submission(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        answers: list[BetAnswerInput],
        submitted_at: datetime,
    ) -> None:
        ...
