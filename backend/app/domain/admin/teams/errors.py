from app.domain.admin.errors import AdminError


class TeamAlreadyExistsError(AdminError):
    def __init__(self, *, code: str):
        self.code = code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"code": self.code}

    @property
    def public_params(self) -> dict:
        return {"code": self.code}


class SeasonNotFoundForSeasonTeamError(AdminError):
    def __init__(self, *, season_year: int):
        self.season_year = season_year
        super().__init__()

    @property
    def context(self) -> dict:
        return {"season_year": self.season_year}

    @property
    def public_params(self) -> dict:
        return {"season_year": self.season_year}


class TeamNotFoundForSeasonTeamError(AdminError):
    def __init__(self, *, team_code: str):
        self.team_code = team_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"team_code": self.team_code}

    @property
    def public_params(self) -> dict:
        return {"team_code": self.team_code}


class SeasonTeamAlreadyExistsError(AdminError):
    def __init__(self, *, season_year: int, team_code: str):
        self.season_year = season_year
        self.team_code = team_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "season_year": self.season_year,
            "team_code": self.team_code,
        }

    @property
    def public_params(self) -> dict:
        return {
            "season_year": self.season_year,
            "team_code": self.team_code,
        }