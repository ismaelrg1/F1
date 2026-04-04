class BetsError(Exception):
    pass


class RaceEventNotFoundForBetQuestionsError(BetsError):
    pass


class BetContextNotFoundForRaceEventError(BetsError):
    pass