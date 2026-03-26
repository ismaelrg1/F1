from typing import Protocol


class SeasonRepository(Protocol):
    def list_seasons(self):
        ...

    def get_active_season(self):
        ...

    def get_season(self, season_id: int):
        ...

    def get_season_roster(self, season_id: int):
        ...
