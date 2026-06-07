from app.domain.bets.errors import BetsError


class PowerUpsRaceEventNotFoundError(BetsError):
    pass


class PowerUpsTestingEventNotFoundError(BetsError):
    pass


class PowerUpsSeasonNotFoundError(BetsError):
    pass


class PowerUpsBetContextNotFoundError(BetsError):
    pass


class PowerUpsRaceEventSessionNotFoundError(BetsError):
    pass


class PowerUpsTestingEventSessionNotFoundError(BetsError):
    pass