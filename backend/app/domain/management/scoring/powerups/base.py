from app.domain.management.scoring.models import (
    PowerUpEffect,
    PowerUpEvaluationContext,
)


class BasePowerUpEvaluator:
    powerup_code: str | None = None
    _registry: dict[str, type["BasePowerUpEvaluator"]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.powerup_code:
            BasePowerUpEvaluator._registry[cls.powerup_code] = cls

    @classmethod
    def get(cls, powerup_code: str) -> "BasePowerUpEvaluator":
        evaluator_cls = cls._registry.get(powerup_code)
        if evaluator_cls is None:
            return NoOpPowerUpEvaluator()
        return evaluator_cls()

    def evaluate(self, context: PowerUpEvaluationContext) -> list[PowerUpEffect]:
        raise NotImplementedError


class NoOpPowerUpEvaluator(BasePowerUpEvaluator):
    def evaluate(self, context: PowerUpEvaluationContext) -> list[PowerUpEffect]:
        return []