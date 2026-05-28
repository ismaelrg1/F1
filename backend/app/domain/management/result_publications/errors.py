from app.domain.management.errors import ManagementError


class ResultPublicationBetContextNotFoundError(ManagementError):
    pass


class ResultPublicationEventSessionNotFoundError(ManagementError):
    pass


class ResultPublicationTestingEventSessionNotFoundError(ManagementError):
    pass


class ResultPublicationOfficialResultsNotFoundError(ManagementError):
    pass


class ResultPublicationAlreadyExistsError(ManagementError):
    pass


class ResultPublicationNotFoundError(ManagementError):
    pass

class ResultPublicationForbiddenGroupError(ManagementError):
    pass

class ResultPublicationScoringRequiredError(ManagementError):
    pass