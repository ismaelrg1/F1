from app.domain.bets.errors import BetAnswerRelationViolationError
from app.domain.bets.shared.models import BetScoreRelationDefinition
from app.domain.bets.answers.relation_validators.base import BetScoreRelationValidator


class DistinctRelationValidator(BetScoreRelationValidator):
    relation_type = "DISTINCT"

    def validate(
        self,
        *,
        relation: BetScoreRelationDefinition,
        source_value: str,
        target_value: str,
    ) -> None:
        if source_value == target_value:
            raise BetAnswerRelationViolationError(
                source_code=relation.source_bet_score_code,
                target_code=relation.target_bet_score_code,
                relation_type=relation.relation_type,
            )