from typing import Protocol

from app.domain.seasons.models import SeasonRoster, SeasonSummary


class SeasonRepository(Protocol):
    def list_seasons(self) -> list[SeasonSummary]:
        ...

    def get_active_season(self) -> SeasonSummary | None:
        ...

    def get_season(self, season_id: int) -> SeasonSummary | None:
        ...

    def get_season_roster(self, season_id: int) -> SeasonRoster | None:
        ...

