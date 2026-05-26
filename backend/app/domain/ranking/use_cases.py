from app.domain.ranking.errors import SeasonNotFoundForRankingError
from app.domain.ranking.models import RankingResult
from app.domain.ranking.ports import RankingRepository


class GetRanking:
    def __init__(self, repository: RankingRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> RankingResult:
        result = self._repository.get_ranking(
            group_id=group_id,
            season_year=season_year,
        )

        if result is None:
            raise SeasonNotFoundForRankingError()

        return result