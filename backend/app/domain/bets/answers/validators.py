from collections.abc import Iterable

from app.domain.bets.answers.models import BetAnswerInput
from app.domain.bets.answers.relation_validators.registry import VALIDATORS_BY_TYPE
from app.domain.bets.shared.models import BetAnswerResult, BetScoreRelationDefinition


class BetAnswerRelationsValidator:
    def validate(
        self,
        *,
        allowed_score_codes: set[str],
        existing_answers: Iterable[BetAnswerResult],
        received_answers: Iterable[BetAnswerInput],
        relations: Iterable[BetScoreRelationDefinition],
    ) -> None:
        answers_by_code = {
            answer.bet_score_code: answer.value
            for answer in existing_answers
            if answer.bet_score_code in allowed_score_codes
        }

        answers_by_code.update(
            {
                answer.bet_score_code: answer.value
                for answer in received_answers
                if answer.bet_score_code in allowed_score_codes
            }
        )

        for relation in relations:
            source_value = answers_by_code.get(relation.source_bet_score_code)
            target_value = answers_by_code.get(relation.target_bet_score_code)

            if source_value is None or target_value is None:
                continue

            validator = VALIDATORS_BY_TYPE.get(relation.relation_type)
            if validator is None:
                continue

            validator.validate(
                relation=relation,
                source_value=source_value,
                target_value=target_value,
            )