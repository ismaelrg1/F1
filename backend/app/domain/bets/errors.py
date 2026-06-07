class BetsError(Exception):
    @property
    def context(self) -> dict:
        return {}

    @property
    def public_params(self) -> dict:
        return {}

    @property
    def log_level(self) -> str:
        return "warning"


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


class TestingEventNotFoundForBetResultsError(BetsError):
    pass


class TestingEventSessionNotFoundForBetResultsError(BetsError):
    pass


class BetContextNotFoundForTestingEventResultsError(BetsError):
    pass

class SeasonNotFoundForBetResultsError(BetsError):
    pass


class BetContextNotFoundForSeasonResultsError(BetsError):
    pass

class RaceEventNotFoundForBetAnswersError(BetsError):
    pass


class TestingEventNotFoundForBetAnswersError(BetsError):
    pass


class SeasonNotFoundForBetAnswersError(BetsError):
    pass