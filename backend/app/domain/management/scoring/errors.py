from app.domain.management.errors import ManagementError


class ScoringBetContextNotFoundError(ManagementError):
    pass


class ScoringOfficialResultsRequiredError(ManagementError):
    pass


class ScoringEvaluatorNotFoundError(ManagementError):
    def __init__(self, evaluator_key: str):
        self.evaluator_key = evaluator_key

    @property
    def public_params(self) -> dict:
        return {"evaluator_key": self.evaluator_key}