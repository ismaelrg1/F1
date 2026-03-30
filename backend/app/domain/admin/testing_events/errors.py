from app.domain.admin.errors import AdminError


class SeasonNotFoundForTestingEventError(AdminError):
    def __init__(self, season_year: int):
        self.season_year = season_year
        super().__init__()

    @property
    def context(self) -> dict:
        return {"season_year": self.season_year}

    @property
    def public_params(self) -> dict:
        return {"season_year": self.season_year}


class CircuitNotFoundForTestingEventError(AdminError):
    def __init__(self, circuit_code: str):
        self.circuit_code = circuit_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"circuit_code": self.circuit_code}

    @property
    def public_params(self) -> dict:
        return {"circuit_code": self.circuit_code}


class TestingEventAlreadyExistsError(AdminError):
    def __init__(self, *, season_year: int, name: str):
        self.season_year = season_year
        self.name = name
        super().__init__()

    @property
    def context(self) -> dict:
        return {"season_year": self.season_year, "name": self.name}

    @property
    def public_params(self) -> dict:
        return {"season_year": self.season_year, "name": self.name}


class DuplicateTestingEventSessionOrderError(AdminError):
    def __init__(self, session_order: int):
        self.session_order = session_order
        super().__init__()

    @property
    def context(self) -> dict:
        return {"session_order": self.session_order}

    @property
    def public_params(self) -> dict:
        return {"session_order": self.session_order}
