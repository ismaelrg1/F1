from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.domain.management.scoring.errors import ScoringEvaluatorNotFoundError


@dataclass(frozen=True)
class ExtraEvaluationDataset:
    scope: Any
    rule: Any
    bets: list[Any]
    scores_by_user: dict[int, Any]
    score_sessions_by_key: dict[tuple[int, int | None, int | None], Any]


@dataclass(frozen=True)
class ExtraEvaluationEffect:
    user_id: int
    points: Decimal
    code: str
    details: dict[str, Any]
    event_session_id: int | None = None
    testing_event_session_id: int | None = None


class BaseExtraEvaluator:
    evaluator_key: str | None = None
    _registry: dict[str, type["BaseExtraEvaluator"]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.evaluator_key:
            BaseExtraEvaluator._registry[cls.evaluator_key] = cls

    @classmethod
    def get(cls, evaluator_key: str) -> "BaseExtraEvaluator":
        evaluator_cls = cls._registry.get(evaluator_key)
        if evaluator_cls is None:
            raise ScoringEvaluatorNotFoundError(evaluator_key)
        return evaluator_cls()

    @classmethod
    def supports(cls, evaluator_key: str) -> bool:
        return evaluator_key in cls._registry

    def evaluate_many(self, dataset: ExtraEvaluationDataset) -> list[ExtraEvaluationEffect]:
        raise NotImplementedError
