from typing import Protocol
from uuid import UUID

from app.domain.bets.shared.models import (
    BetContextDefinition,
    BetRaceEvent,
    BetSeason,
    BetTemplateDefinition,
    BetTestingEvent,
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
