from app.domain.bets.answers.relation_validators.base import BetScoreRelationValidator
from app.domain.bets.answers.relation_validators.distinct import DistinctRelationValidator
from app.domain.bets.answers.relation_validators.less_than_or_equal import (
    LessThanOrEqualRelationValidator,
)
from app.domain.bets.answers.relation_validators.matches_position import (
    MatchesPositionRelationValidator,
)


_RELATION_VALIDATORS: list[BetScoreRelationValidator] = [
    DistinctRelationValidator(),
    MatchesPositionRelationValidator(),
    LessThanOrEqualRelationValidator(),
]


VALIDATORS_BY_TYPE = {
    validator.relation_type: validator
    for validator in _RELATION_VALIDATORS
}