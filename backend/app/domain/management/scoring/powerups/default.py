from decimal import Decimal

from app.domain.management.scoring.models import (
    PowerUpEffect,
    PowerUpEvaluationContext,
)
from app.domain.management.scoring.powerups.base import BasePowerUpEvaluator


class DoublePointsPowerUpEvaluator(BasePowerUpEvaluator):
    powerup_code = "DOUBLE_POINTS"

    def evaluate(self, context: PowerUpEvaluationContext) -> list[PowerUpEffect]:
        base_points = context.base_points_by_user.get(context.actor_user_id, Decimal("0"))
        if base_points <= 0:
            return []

        return [
            PowerUpEffect(
                target_user_id=context.actor_user_id,
                component_type="POWERUP",
                code=context.powerup_code,
                points=base_points,
                details={
                    "powerup_code": context.powerup_code,
                    "actor_user_id": context.actor_user_id,
                    "multiplier": 2,
                    "base_points": str(base_points),
                },
            )
        ]


class HalfPointsPenaltyPowerUpEvaluator(BasePowerUpEvaluator):
    powerup_code = "HALVE_POINTS"

    def evaluate(self, context: PowerUpEvaluationContext) -> list[PowerUpEffect]:
        effects: list[PowerUpEffect] = []

        for target_user_id in context.target_user_ids:
            base_points = context.base_points_by_user.get(target_user_id, Decimal("0"))
            if base_points <= 0:
                continue

            penalty_points = base_points / Decimal("2")

            effects.append(
                PowerUpEffect(
                    target_user_id=target_user_id,
                    component_type="PENALTY",
                    code=context.powerup_code,
                    points=penalty_points,
                    details={
                        "powerup_code": context.powerup_code,
                        "actor_user_id": context.actor_user_id,
                        "target_user_id": target_user_id,
                        "base_points": str(base_points),
                        "penalty_fraction": "1/2",
                    },
                )
            )

        return effects