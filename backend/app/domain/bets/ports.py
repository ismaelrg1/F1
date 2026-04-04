from typing import Protocol
from uuid import UUID

from app.db.betting import BetContext, BetTemplate
from app.db.competition import RaceEvent


class BetQuestionsRepository(Protocol):
    def get_race_event_by_public_id(self, public_id: UUID) -> RaceEvent | None:
        ...

    def get_gp_bet_context(self, *, group_id: int, race_event_id: int) -> BetContext | None:
        ...

    def list_gp_templates_for_season(self, *, season_id: int) -> list[BetTemplate]:
        ...