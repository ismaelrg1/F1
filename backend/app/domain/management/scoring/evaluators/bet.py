from decimal import Decimal

from app.domain.management.scoring.evaluators.base import BaseEvaluator, EvaluationResult


class ExactMatchEvaluator(BaseEvaluator):
    evaluator_key = "exact_match"

    def evaluate(self, *, pick, official_result, bet_score, rule, relations=None, related_picks=None) -> EvaluationResult:
        params = rule.params_json if rule is not None and rule.params_json else {}
        points = Decimal(str(params.get("points", bet_score.base_points)))

        hit = pick.value == official_result.value

        details = {
            "answer": pick.value,
            "official": official_result.value,
            "evaluator_key": self.evaluator_key,
        }

        if "special_group" in params:
            details["special_group"] = params["special_group"]

        return EvaluationResult(
            points=points if hit else Decimal("0"),
            hit=hit,
            details=details,
        )
    
class PositionExactOrDnfEvaluator(BaseEvaluator):
    evaluator_key = "position_exact_or_dnf"

    def evaluate(self, *, pick, official_result, bet_score, rule, relations=None, related_picks=None) -> EvaluationResult:
        params = rule.params_json if rule is not None and rule.params_json else {}
        exact_points = Decimal(str(params.get("points", bet_score.base_points)))
        dnf_value = params.get("dnf_value", "DNF")
        dnf_points = Decimal(str(params.get("dnf_points", 0)))

        hit = pick.value == official_result.value
        if not hit:
            points = Decimal("0")
        elif official_result.value == dnf_value:
            points = dnf_points
        else:
            points = exact_points

        details = {
            "answer": pick.value,
            "official": official_result.value,
            "evaluator_key": self.evaluator_key,
            "dnf_value": dnf_value,
        }

        if "special_group" in params:
            details["special_group"] = params["special_group"]

        return EvaluationResult(points=points, hit=hit, details=details)


class PositionExactOrNearEvaluator(BaseEvaluator):
    evaluator_key = "position_exact_or_near"

    def evaluate(self, *, pick, official_result, bet_score, rule, relations=None, related_picks=None) -> EvaluationResult:
        params = rule.params_json if rule is not None and rule.params_json else {}
        exact_points = Decimal(str(params.get("points", bet_score.base_points)))
        near_points = Decimal(str(params.get("near_points", 0)))
        near_delta = int(params.get("near_delta", 1))

        try:
            answer = int(pick.value)
            official = int(official_result.value)
        except ValueError:
            return EvaluationResult(
                points=Decimal("0"),
                hit=False,
                details={
                    "answer": pick.value,
                    "official": official_result.value,
                    "evaluator_key": self.evaluator_key,
                    "reason": "invalid_position_value",
                },
            )

        if answer == official:
            points = exact_points
            hit = True
            near_hit = False
        elif abs(answer - official) <= near_delta:
            points = near_points
            hit = False
            near_hit = True
        else:
            points = Decimal("0")
            hit = False
            near_hit = False

        details = {
            "answer": pick.value,
            "official": official_result.value,
            "evaluator_key": self.evaluator_key,
            "near_delta": near_delta,
            "near_hit": near_hit,
        }

        if "special_group" in params:
            details["special_group"] = params["special_group"]

        return EvaluationResult(points=points, hit=hit, details=details)