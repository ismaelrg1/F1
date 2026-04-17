from typing import Protocol

from app.domain.seasons.models import SeasonSummary


class SeasonRepository(Protocol):
    def list_seasons(self) -> list[SeasonSummary]:
        ...

    def get_active_season(self) -> SeasonSummary | None:
        ...

    def get_season(self, season_id: int) -> SeasonSummary | None:
        ...
