from dataclasses import dataclass
from decimal import Decimal

from app.domain.management.scoring.errors import ScoringEvaluatorNotFoundError


@dataclass(frozen=True)
class EvaluationResult:
    points: Decimal
    hit: bool
    details: dict


class BaseEvaluator:
    evaluator_key: str | None = None
    _registry: dict[str, type["BaseEvaluator"]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.evaluator_key:
            BaseEvaluator._registry[cls.evaluator_key] = cls

    @classmethod
    def get(cls, evaluator_key: str) -> "BaseEvaluator":
        evaluator_cls = cls._registry.get(evaluator_key)
        if evaluator_cls is None:
            raise ScoringEvaluatorNotFoundError(evaluator_key)
        return evaluator_cls()

    def evaluate(self, *, pick, official_result, bet_score, rule) -> EvaluationResult:
        raise NotImplementedError