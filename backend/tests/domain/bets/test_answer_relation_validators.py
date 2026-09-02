from app.domain.bets.answers.models import BetAnswerInput
from app.domain.bets.answers.validators import BetAnswerRelationsValidator
from app.domain.bets.errors import BetAnswerRelationViolationError
from app.domain.bets.shared.models import BetAnswerResult, BetScoreRelationDefinition


def _relation(
    *,
    source_code: str,
    target_code: str,
    relation_type: str,
    config_json: dict | None = None,
) -> BetScoreRelationDefinition:
    return BetScoreRelationDefinition(
        source_bet_score_code=source_code,
        target_bet_score_code=target_code,
        relation_type=relation_type,
        config_json=config_json,
    )


def test_answer_relation_validator_rejects_distinct_violation() -> None:
    validator = BetAnswerRelationsValidator()

    try:
        validator.validate(
            allowed_score_codes={"WINNER", "SECOND"},
            existing_answers=[],
            received_answers=[
                BetAnswerInput(bet_score_code="WINNER", value="VER"),
                BetAnswerInput(bet_score_code="SECOND", value="VER"),
            ],
            relations=[
                _relation(
                    source_code="WINNER",
                    target_code="SECOND",
                    relation_type="DISTINCT",
                )
            ],
        )
    except BetAnswerRelationViolationError as exc:
        assert exc.source_code == "WINNER"
        assert exc.target_code == "SECOND"
        assert exc.relation_type == "DISTINCT"
    else:
        raise AssertionError("BetAnswerRelationViolationError was not raised")


def test_answer_relation_validator_allows_partial_answers() -> None:
    validator = BetAnswerRelationsValidator()

    validator.validate(
        allowed_score_codes={"WINNER", "POSITION_VER"},
        existing_answers=[],
        received_answers=[
            BetAnswerInput(bet_score_code="WINNER", value="VER"),
        ],
        relations=[
            _relation(
                source_code="WINNER",
                target_code="POSITION_VER",
                relation_type="MATCHES_POSITION",
                config_json={"driver_code": "VER", "position": 1},
            )
        ],
    )


def test_answer_relation_validator_rejects_matches_position_violation() -> None:
    validator = BetAnswerRelationsValidator()

    try:
        validator.validate(
            allowed_score_codes={"WINNER", "POSITION_VER"},
            existing_answers=[],
            received_answers=[
                BetAnswerInput(bet_score_code="WINNER", value="VER"),
                BetAnswerInput(bet_score_code="POSITION_VER", value="2"),
            ],
            relations=[
                _relation(
                    source_code="WINNER",
                    target_code="POSITION_VER",
                    relation_type="MATCHES_POSITION",
                    config_json={"driver_code": "VER", "position": 1},
                )
            ],
        )
    except BetAnswerRelationViolationError as exc:
        assert exc.source_code == "WINNER"
        assert exc.target_code == "POSITION_VER"
        assert exc.relation_type == "MATCHES_POSITION"
    else:
        raise AssertionError("BetAnswerRelationViolationError was not raised")


def test_answer_relation_validator_rejects_less_than_or_equal_violation() -> None:
    validator = BetAnswerRelationsValidator()

    try:
        validator.validate(
            allowed_score_codes={"PRETEST_NUM_RF_ONE_DAY", "PRETEST_NUM_RF"},
            existing_answers=[
                BetAnswerResult(
                    bet_score_code="PRETEST_NUM_RF",
                    value="3",
                )
            ],
            received_answers=[
                BetAnswerInput(
                    bet_score_code="PRETEST_NUM_RF_ONE_DAY",
                    value="4",
                )
            ],
            relations=[
                _relation(
                    source_code="PRETEST_NUM_RF_ONE_DAY",
                    target_code="PRETEST_NUM_RF",
                    relation_type="LESS_THAN_OR_EQUAL",
                )
            ],
        )
    except BetAnswerRelationViolationError as exc:
        assert exc.source_code == "PRETEST_NUM_RF_ONE_DAY"
        assert exc.target_code == "PRETEST_NUM_RF"
        assert exc.relation_type == "LESS_THAN_OR_EQUAL"
    else:
        raise AssertionError("BetAnswerRelationViolationError was not raised")
