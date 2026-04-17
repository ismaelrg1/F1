from app.domain.seasons.models import SeasonRoster, SeasonSummary
from app.domain.seasons.ports import SeasonRepository


class ListSeasons:
    def __init__(self, repository: SeasonRepository):
        self._repository = repository

    def execute(self) -> list[SeasonSummary]:
        return self._repository.list_seasons()


class GetActiveSeason:
    def __init__(self, repository: SeasonRepository):
        self._repository = repository

    def execute(self) -> SeasonSummary | None:
        return self._repository.get_active_season()


class GetSeason:
    def __init__(self, repository: SeasonRepository):
        self._repository = repository

    def execute(self, season_id: int) -> SeasonSummary | None:
        return self._repository.get_season(season_id)


class GetSeasonRoster:
    def __init__(self, repository: SeasonRepository):
        self._repository = repository

    def execute(self, season_id: int) -> SeasonRoster | None:
        return self._repository.get_season_roster(season_id)
