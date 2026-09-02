from abc import ABC, abstractmethod

from app.domain.bets.shared.models import BetScoreRelationDefinition


class BetScoreRelationValidator(ABC):
    relation_type: str

    @abstractmethod
    def validate(
        self,
        *,
        relation: BetScoreRelationDefinition,
        source_value: str,
        target_value: str,
    ) -> None:
        ...