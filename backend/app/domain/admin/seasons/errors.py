from app.domain.admin.errors import AdminError


class SeasonAlreadyExistsError(AdminError):
    def __init__(self, *, year: int):
        self.year = year
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "year": self.year,
        }

    @property
    def public_params(self) -> dict:
        return {
            "year": self.year,
        }


class ActiveSeasonAlreadyExistsError(AdminError):
    def __init__(self, *, active_year: int):
        self.active_year = active_year
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "active_year": self.active_year,
        }

    @property
    def public_params(self) -> dict:
        return {
            "active_year": self.active_year,
        }
