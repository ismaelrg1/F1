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

class BetAnswersNotOpenError(BetsError):
    pass

class BetAnswersClosedError(BetsError):
    pass


class BetAnswerQuestionNotFoundError(BetsError):
    pass


class BetAlreadySubmittedError(BetsError):
    pass

class BetRequiredAnswerMissingError(BetsError):
    pass


class BetModificationLimitReachedError(BetsError):
    pass

# Results

class RaceEventNotFoundForBetResultsError(BetsError):
    pass


class RaceEventSessionNotFoundForBetResultsError(BetsError):
    pass


class BetContextNotFoundForRaceEventResultsError(BetsError):
    pass