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
    def __init__(self, *, country_id: int):
        self.country_id = country_id
        super().__init__()

    @property
    def context(self) -> dict:
        return {"country_id": self.country_id}
    
    @property
    def public_params(self) -> dict:
        return {"country_id": self.country_id}