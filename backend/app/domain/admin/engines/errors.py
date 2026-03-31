from app.domain.admin.errors import AdminError


class EngineAlreadyExistsError(AdminError):
    def __init__(self, *, code: str):
        self.code = code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"code": self.code}

    @property
    def public_params(self) -> dict:
        return {"code": self.code}


class SeasonNotFoundForSeasonEngineError(AdminError):
    def __init__(self, *, season_year: int):
        self.season_year = season_year
        super().__init__()

    @property
    def context(self) -> dict:
        return {"season_year": self.season_year}

    @property
    def public_params(self) -> dict:
        return {"season_year": self.season_year}


class EngineNotFoundForSeasonEngineError(AdminError):
    def __init__(self, *, engine_code: str):
        self.engine_code = engine_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"engine_code": self.engine_code}

    @property
    def public_params(self) -> dict:
        return {"engine_code": self.engine_code}


class SeasonEngineAlreadyExistsError(AdminError):
    def __init__(self, *, season_year: int, engine_code: str):
        self.season_year = season_year
        self.engine_code = engine_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "season_year": self.season_year,
            "engine_code": self.engine_code,
        }

    @property
    def public_params(self) -> dict:
        return {
            "season_year": self.season_year,
            "engine_code": self.engine_code,
        }