from app.domain.admin.errors import AdminError


class CountryAlreadyExistsError(AdminError):
    def __init__(self, *, iso2: str):
        self.iso2 = iso2
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "iso2": self.iso2,
        }

    @property
    def public_params(self) -> dict:
        return {
            "iso2": self.iso2,
        }
