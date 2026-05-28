from decimal import Decimal

from app.domain.management.scoring.evaluators.base import BaseEvaluator, EvaluationResult


class ExactMatchEvaluator(BaseEvaluator):
    evaluator_key = "exact_match"

    def evaluate(self, *, pick, official_result, bet_score, rule) -> EvaluationResult:
        points = Decimal(str(bet_score.base_points))
        hit = pick.value == official_result.value

        return EvaluationResult(
            points=points if hit else Decimal("0"),
            hit=hit,
            details={
                "answer": pick.value,
                "official": official_result.value,
                "evaluator_key": self.evaluator_key,
            },
        )