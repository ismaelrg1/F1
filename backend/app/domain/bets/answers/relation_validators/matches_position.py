from app.domain.bets.errors import BetAnswerRelationViolationError
from app.domain.bets.shared.models import BetScoreRelationDefinition
from app.domain.bets.answers.relation_validators.base import BetScoreRelationValidator


class MatchesPositionRelationValidator(BetScoreRelationValidator):
    relation_type = "MATCHES_POSITION"

    def validate(
        self,
        *,
        relation: BetScoreRelationDefinition,
        source_value: str,
        target_value: str,
    ) -> None:
        config = relation.config_json or {}
        driver_code = config.get("driver_code")
        expected_position = config.get("position")

        if driver_code is None or expected_position is None:
            return

        if source_value != str(driver_code):
            return

        if target_value != str(expected_position):
            raise BetAnswerRelationViolationError(
                source_code=relation.source_bet_score_code,
                target_code=relation.target_bet_score_code,
                relation_type=relation.relation_type,
            )