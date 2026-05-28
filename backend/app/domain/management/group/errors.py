from app.domain.management.errors import ManagementError


class ManagementGroupRequiredError(ManagementError):
    pass


class ManagementForbiddenGroupError(ManagementError):
    pass
