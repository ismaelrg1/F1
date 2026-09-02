from app.domain.bets.errors import BetAnswerRelationViolationError
from app.domain.bets.shared.models import BetScoreRelationDefinition
from app.domain.bets.answers.relation_validators.base import BetScoreRelationValidator


class LessThanOrEqualRelationValidator(BetScoreRelationValidator):
    relation_type = "LESS_THAN_OR_EQUAL"

    def validate(
        self,
        *,
        relation: BetScoreRelationDefinition,
        source_value: str,
        target_value: str,
    ) -> None:
        try:
            source_number = float(source_value)
            target_number = float(target_value)
        except ValueError:
            raise BetAnswerRelationViolationError(
                source_code=relation.source_bet_score_code,
                target_code=relation.target_bet_score_code,
                relation_type=relation.relation_type,
            )

        if source_number > target_number:
            raise BetAnswerRelationViolationError(
                source_code=relation.source_bet_score_code,
                target_code=relation.target_bet_score_code,
                relation_type=relation.relation_type,
            )