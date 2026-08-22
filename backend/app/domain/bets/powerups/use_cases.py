from uuid import UUID

from app.domain.bets.powerups.errors import (
    PowerUpsBetContextNotFoundError,
    PowerUpsRaceEventNotFoundError,
    PowerUpsRaceEventSessionNotFoundError,
    PowerUpsSeasonNotFoundError,
    PowerUpsTestingEventNotFoundError,
    PowerUpsTestingEventSessionNotFoundError,
)
from app.db.enums import PowerUpTargetType
from app.domain.bets.powerups.models import BetPowerUpsResult, BetPowerUpAvailability, BetPowerUpTargetOption
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

        powerups = self._repository.list_available_powerups(
            group_id=group_id,
            user_id=user_id,
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=None,
        )

        return BetPowerUpsResult(
            race_event_public_id=race_event_public_id,
            powerups=BetPowerUpTargetOptionsResolver(self._repository).add_target_options(
                group_id=group_id,
                actor_user_id=user_id,
                bet_context_id=bet_context_id,
                powerups=powerups,
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

        powerups = self._repository.list_available_powerups(
            group_id=group_id,
            user_id=user_id,
            bet_context_id=bet_context_id,
            event_session_id=None,
            testing_event_session_id=testing_event_session_id,
        )

        return BetPowerUpsResult(
            testing_event_public_id=testing_event_public_id,
            powerups=BetPowerUpTargetOptionsResolver(self._repository).add_target_options(
                group_id=group_id,
                actor_user_id=user_id,
                bet_context_id=bet_context_id,
                powerups=powerups,
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

        powerups = self._repository.list_available_powerups(
            group_id=group_id,
            user_id=user_id,
            bet_context_id=bet_context_id,
            event_session_id=None,
            testing_event_session_id=None,
        )

        return BetPowerUpsResult(
            season_year=season_year,
            powerups=BetPowerUpTargetOptionsResolver(self._repository).add_target_options(
                group_id=group_id,
                actor_user_id=user_id,
                bet_context_id=bet_context_id,
                powerups=powerups,
            ),
        )
    
class BetPowerUpTargetOptionsResolver:
    def __init__(self, repository: BetPowerUpsRepository) -> None:
        self._repository = repository

    def add_target_options(
        self,
        *,
        group_id: int,
        actor_user_id: int,
        bet_context_id: int,
        powerups: list[BetPowerUpAvailability],
    ) -> list[BetPowerUpAvailability]:
        result: list[BetPowerUpAvailability] = []

        for powerup in powerups:
            result.append(
                BetPowerUpAvailability(
                    powerup_id=powerup.powerup_id,
                    code=powerup.code,
                    name=powerup.name,
                    target_mode=powerup.target_mode,
                    quantity=powerup.quantity,
                    is_enabled=powerup.is_enabled,
                    is_restricted=powerup.is_restricted,
                    already_used=powerup.already_used,
                    target_options=self._resolve_for_powerup(
                        group_id=group_id,
                        actor_user_id=actor_user_id,
                        bet_context_id=bet_context_id,
                        powerup=powerup,
                    ),
                )
            )

        return result

    def _resolve_for_powerup(
        self,
        *,
        group_id: int,
        actor_user_id: int,
        bet_context_id: int,
        powerup: BetPowerUpAvailability,
    ) -> list[BetPowerUpTargetOption]:
        if powerup.code.startswith("DOUBLE_POINTS"):
            return []

        if powerup.code.startswith("HALVE_POINTS"):
            return self._resolve_user_targets_for_halve_points(
                group_id=group_id,
                actor_user_id=actor_user_id,
                bet_context_id=bet_context_id,
                powerup=powerup,
            )

        return []

    def _resolve_user_targets_for_halve_points(
        self,
        *,
        group_id: int,
        actor_user_id: int,
        bet_context_id: int,
        powerup: BetPowerUpAvailability,
    ) -> list[BetPowerUpTargetOption]:
        users = self._repository.list_group_user_targets(
            group_id=group_id,
            actor_user_id=actor_user_id,
            bet_context_id=bet_context_id,
        )

        options: list[BetPowerUpTargetOption] = []

        for user in users:
            received_contexts = self._repository.count_distinct_contexts_where_user_received_powerup(
                group_id=group_id,
                target_user_id=user.user_id,
                powerup_id=powerup.powerup_id,
                excluding_bet_context_id=bet_context_id,
            )

            is_available = received_contexts < 2

            options.append(
                BetPowerUpTargetOption(
                    target_type=PowerUpTargetType.USER.value,
                    target_user_public_id=user.user_public_id,
                    label=user.username,
                    is_available=is_available,
                    unavailable_reason=None if is_available else "penalty_limit_reached",
                )
            )

        return options
