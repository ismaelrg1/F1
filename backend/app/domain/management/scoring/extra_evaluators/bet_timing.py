from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.domain.management.scoring.extra_evaluators.base import (
    BaseExtraEvaluator,
    ExtraEvaluationDataset,
    ExtraEvaluationEffect,
)


class BonusByOldestLastModifiedEvaluator(BaseExtraEvaluator):
    evaluator_key = "bonus_by_oldest_last_modified"

    def evaluate_many(self, dataset: ExtraEvaluationDataset) -> list[ExtraEvaluationEffect]:
        if not dataset.scope.is_race_event:
            return []

        params = dataset.rule.params_json or {}
        points_by_session_type = params.get("points_by_session_type", {})

        bets_by_session = defaultdict(list)

        for bet in dataset.bets:
            if bet.event_session_id is None:
                continue
            if bet.submitted_at is None:
                continue
            bets_by_session[bet.event_session_id].append(bet)

        effects = []

        for event_session_id, session_bets in bets_by_session.items():
            winning_bet = min(
                session_bets,
                key=lambda bet: (bet.last_modified_at, bet.id),
            )

            score_session = dataset.score_sessions_by_key.get(
                (winning_bet.user_id, event_session_id, None)
            )
            if score_session is None or score_session.event_session is None:
                continue

            session_type = getattr(
                score_session.event_session.session_type,
                "value",
                score_session.event_session.session_type,
            )

            points = Decimal(str(points_by_session_type.get(session_type, 0)))
            if points <= 0:
                continue

            effects.append(
                ExtraEvaluationEffect(
                    user_id=winning_bet.user_id,
                    event_session_id=event_session_id,
                    testing_event_session_id=None,
                    points=points,
                    code=f"{dataset.rule.code}_{session_type}",
                    details={
                        "evaluator_key": self.evaluator_key,
                        "session_type": session_type,
                        "bet_id": winning_bet.id,
                        "last_modified_at": winning_bet.last_modified_at.isoformat(),
                        "scoring_rule_id": dataset.rule.id,
                    },
                )
            )

        return effects