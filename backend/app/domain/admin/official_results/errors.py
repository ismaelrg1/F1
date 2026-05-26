from app.domain.admin.errors import AdminError


class OfficialResultsBetContextNotFoundError(AdminError):
    pass


class OfficialResultsEventSessionNotFoundError(AdminError):
    pass


class OfficialResultsTestingEventSessionNotFoundError(AdminError):
    pass


class OfficialResultsInvalidScopeError(AdminError):
    pass


class OfficialResultsBetScoreNotFoundError(AdminError):
    pass


class OfficialResultsAlreadyExistsError(AdminError):
    pass


class OfficialResultsNotFoundError(AdminError):
    pass