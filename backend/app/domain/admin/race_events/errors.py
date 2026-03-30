from app.domain.admin.errors import AdminError


class SeasonNotFoundForRaceEventError(AdminError):
    def __init__(self, *, season_year: int):
        self.season_year = season_year
        super().__init__()

    @property
    def context(self) -> dict:
        return {"season_year": self.season_year}

    @property
    def public_params(self) -> dict:
        return {"season_year": self.season_year}


class CircuitNotFoundForRaceEventError(AdminError):
    def __init__(self, *, circuit_code: str):
        self.circuit_code = circuit_code
        super().__init__()

    @property
    def context(self) -> dict:
        return {"circuit_code": self.circuit_code}

    @property
    def public_params(self) -> dict:
        return {"circuit_code": self.circuit_code}


class RaceEventAlreadyExistsError(AdminError):
    def __init__(self, *, season_year: int, round_number: int):
        self.season_year = season_year
        self.round_number = round_number
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "season_year": self.season_year,
            "round_number": self.round_number,
        }

    @property
    def public_params(self) -> dict:
        return {
            "season_year": self.season_year,
            "round_number": self.round_number,
        }


class DuplicateRaceEventSessionTypeError(AdminError):
    def __init__(self, *, session_type: str):
        self.session_type = session_type
        super().__init__()

    @property
    def context(self) -> dict:
        return {"session_type": self.session_type}

    @property
    def public_params(self) -> dict:
        return {"session_type": self.session_type}