class BetsError(Exception):
    pass


class RaceEventNotFoundForBetQuestionsError(BetsError):
    pass


class BetContextNotFoundForRaceEventError(BetsError):
    pass


class TestingEventNotFoundForBetQuestionsError(BetsError):
    pass


class BetContextNotFoundForTestingEventError(BetsError):
    pass

class SeasonNotFoundForBetQuestionsError(BetsError):
    pass

class BetContextNotFoundForSeasonError(BetsError):
    pass