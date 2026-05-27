from app.domain.management.errors import ManagementError


class OfficialResultsBetContextNotFoundError(ManagementError):
    pass


class OfficialResultsEventSessionNotFoundError(ManagementError):
    pass


class OfficialResultsTestingEventSessionNotFoundError(ManagementError):
    pass


class OfficialResultsInvalidScopeError(ManagementError):
    pass


class OfficialResultsBetScoreNotFoundError(ManagementError):
    pass


class OfficialResultsAlreadyExistsError(ManagementError):
    pass


class OfficialResultsNotFoundError(ManagementError):
    pass

class OfficialResultsForbiddenGroupError(ManagementError):
    pass