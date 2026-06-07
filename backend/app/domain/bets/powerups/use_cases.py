from uuid import UUID

from app.domain.bets.powerups.errors import (
    PowerUpsBetContextNotFoundError,
    PowerUpsRaceEventNotFoundError,
    PowerUpsRaceEventSessionNotFoundError,
    PowerUpsSeasonNotFoundError,
    PowerUpsTestingEventNotFoundError,
    PowerUpsTestingEventSessionNotFoundError,
)
from app.domain.bets.powerups.models import BetPowerUpsResult
from app.domain.bets.powerups.ports import BetPowerUpsRepository


class GetRaceEventPowerUps:
    def __init__(self, repository: BetPowerUpsRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        user_id: int,
        race_event_public_id: UUID,
        event_session_public_id: UUID | None,
    ) -> BetPowerUpsResult:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise PowerUpsRaceEventNotFoundError()

        bet_context_id = self._repository.get_race_bet_context_id(
            group_id=group_id,
            race_event_id=race_event.id,
        )
        if bet_context_id is None:
            raise PowerUpsBetContextNotFoundError()

        event_session_id = None
        if event_session_public_id is not None:
            event_session_id = self._repository.get_event_session_id(
                race_event_id=race_event.id,
                event_session_public_id=event_session_public_id,
            )
            if event_session_id is None:
                raise PowerUpsRaceEventSessionNotFoundError()

        return BetPowerUpsResult(
            race_event_public_id=race_event_public_id,
            powerups=self._repository.list_available_powerups(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=None,
            ),
        )


class GetTestingEventPowerUps:
    def __init__(self, repository: BetPowerUpsRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        user_id: int,
        testing_event_public_id: UUID,
        testing_event_session_public_id: UUID | None,
    ) -> BetPowerUpsResult:
        testing_event = self._repository.get_testing_event_by_public_id(testing_event_public_id)
        if testing_event is None:
            raise PowerUpsTestingEventNotFoundError()

        bet_context_id = self._repository.get_testing_bet_context_id(
            group_id=group_id,
            testing_event_id=testing_event.id,
        )
        if bet_context_id is None:
            raise PowerUpsBetContextNotFoundError()

        testing_event_session_id = None
        if testing_event_session_public_id is not None:
            testing_event_session_id = self._repository.get_testing_event_session_id(
                testing_event_id=testing_event.id,
                testing_event_session_public_id=testing_event_session_public_id,
            )
            if testing_event_session_id is None:
                raise PowerUpsTestingEventSessionNotFoundError()

        return BetPowerUpsResult(
            testing_event_public_id=testing_event_public_id,
            powerups=self._repository.list_available_powerups(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=None,
                testing_event_session_id=testing_event_session_id,
            ),
        )


class GetSeasonPowerUps:
    def __init__(self, repository: BetPowerUpsRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        user_id: int,
        season_year: int,
    ) -> BetPowerUpsResult:
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise PowerUpsSeasonNotFoundError()

        bet_context_id = self._repository.get_season_bet_context_id(
            group_id=group_id,
            season_id=season.id,
        )
        if bet_context_id is None:
            raise PowerUpsBetContextNotFoundError()

        return BetPowerUpsResult(
            season_year=season_year,
            powerups=self._repository.list_available_powerups(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=None,
                testing_event_session_id=None,
            ),
        )