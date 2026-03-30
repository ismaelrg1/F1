from app.domain.admin.errors import AdminError

class CircuitAlreadyExistsError(AdminError):
    def __init__(self, *, code: str):
        self.code = code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"code": self.code}
    
    @property
    def public_params(self) -> dict:
        return {"code": self.code}
    
class CountryNotFoundForCircuitError(AdminError):
    def __init__(self, *, country_iso2: str):
        self.country_iso2 = country_iso2
        super().__init__()

    @property
    def context(self) -> dict:
        return {"country_iso2": self.country_iso2}
    
    @property
    def public_params(self) -> dict:
        return {"country_iso2": self.country_iso2}
