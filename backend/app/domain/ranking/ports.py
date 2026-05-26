from typing import Protocol

from app.domain.ranking.models import RankingResult


class RankingRepository(Protocol):
    def get_ranking(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> RankingResult | None:
        ...