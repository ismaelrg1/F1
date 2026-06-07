from typing import Protocol
from uuid import UUID

from app.domain.bets.powerups.models import BetPowerUpAvailability
from app.domain.bets.shared.models import BetRaceEvent, BetSeason, BetTestingEvent


class BetPowerUpsRepository(Protocol):
    def get_race_event_by_public_id(self, public_id: UUID) -> BetRaceEvent | None:
        ...

    def get_testing_event_by_public_id(self, public_id: UUID) -> BetTestingEvent | None:
        ...

    def get_season_by_year(self, year: int) -> BetSeason | None:
        ...

    def get_race_bet_context_id(
        self,
        *,
        group_id: int,
        race_event_id: int,
    ) -> int | None:
        ...

    def get_testing_bet_context_id(
        self,
        *,
        group_id: int,
        testing_event_id: int,
    ) -> int | None:
        ...

    def get_season_bet_context_id(
        self,
        *,
        group_id: int,
        season_id: int,
    ) -> int | None:
        ...

    def get_event_session_id(
        self,
        *,
        race_event_id: int,
        event_session_public_id: UUID,
    ) -> int | None:
        ...

    def get_testing_event_session_id(
        self,
        *,
        testing_event_id: int,
        testing_event_session_public_id: UUID,
    ) -> int | None:
        ...

    def list_available_powerups(
        self,
        *,
        group_id: int,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> list[BetPowerUpAvailability]:
        ...