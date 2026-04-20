class BetsError(Exception):
    pass


class RaceEventNotFoundForBetQuestionsError(BetsError):
    pass


class RaceEventSessionNotFoundForBetAnswersError(BetsError):
    pass


class BetContextNotFoundForRaceEventError(BetsError):
    pass


class TestingEventNotFoundForBetQuestionsError(BetsError):
    pass


class TestingEventSessionNotFoundForBetAnswersError(BetsError):
    pass


class BetContextNotFoundForTestingEventError(BetsError):
    pass


class SeasonNotFoundForBetQuestionsError(BetsError):
    pass


class BetContextNotFoundForSeasonError(BetsError):
    pass
