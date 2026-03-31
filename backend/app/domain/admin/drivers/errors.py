from app.domain.admin.errors import AdminError


class DriverAlreadyExistsError(AdminError):
    def __init__(self, *, code: str):
        self.code = code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"code": self.code}

    @property
    def public_params(self) -> dict:
        return {"code": self.code}


class SeasonNotFoundForSeasonDriverError(AdminError):
    def __init__(self, *, season_year: int):
        self.season_year = season_year
        super().__init__()

    @property
    def context(self) -> dict:
        return {"season_year": self.season_year}

    @property
    def public_params(self) -> dict:
        return {"season_year": self.season_year}


class DriverNotFoundForSeasonDriverError(AdminError):
    def __init__(self, *, driver_code: str):
        self.driver_code = driver_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"driver_code": self.driver_code}

    @property
    def public_params(self) -> dict:
        return {"driver_code": self.driver_code}


class SeasonDriverAlreadyExistsError(AdminError):
    def __init__(self, *, season_year: int, driver_code: str):
        self.season_year = season_year
        self.driver_code = driver_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "season_year": self.season_year,
            "driver_code": self.driver_code,
        }

    @property
    def public_params(self) -> dict:
        return {
            "season_year": self.season_year,
            "driver_code": self.driver_code,
        }