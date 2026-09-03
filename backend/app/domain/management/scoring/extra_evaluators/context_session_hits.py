from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.db.enums import ScoreComponentType
from app.domain.management.scoring.extra_evaluators.base import (
    BaseExtraEvaluator,
    ExtraEvaluationDataset,
    ExtraEvaluationEffect,
)


class BonusIfContextSessionHitsGteEvaluator(BaseExtraEvaluator):
    evaluator_key = "bonus_if_context_session_hits_gte"

    def evaluate_many(self, dataset: ExtraEvaluationDataset) -> list[ExtraEvaluationEffect]:
        if not dataset.scope.is_race_event:
            return []

        params = dataset.rule.params_json or {}
        hits_gte = int(params.get("hits_gte", 0))
        points = Decimal(str(params.get("points", 0)))

        stats_by_user = defaultdict(lambda: {"hits_count": 0, "picks_count": 0})

        for (user_id, event_session_id, testing_event_session_id), score_session in dataset.score_sessions_by_key.items():
            if event_session_id is None or testing_event_session_id is not None:
                continue

            for component in score_session.score_session_components:
                if component.component_type != ScoreComponentType.BASE:
                    continue

                stats_by_user[user_id]["picks_count"] += 1
                if component.details_json.get("hit") is True:
                    stats_by_user[user_id]["hits_count"] += 1

        effects = []

        for user_id, stats in stats_by_user.items():
            if stats["hits_count"] < hits_gte:
                continue

            effects.append(
                ExtraEvaluationEffect(
                    user_id=user_id,
                    points=points,
                    code=dataset.rule.code,
                    details={
                        "evaluator_key": self.evaluator_key,
                        "hits_count": stats["hits_count"],
                        "picks_count": stats["picks_count"],
                        "hits_gte": hits_gte,
                        "scoring_rule_id": dataset.rule.id,
                    },
                )
            )

        return effects