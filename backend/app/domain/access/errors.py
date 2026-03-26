class AccessError(Exception):
    @property
    def context(self) -> dict:
        return {}
    
    @property
    def public_params(self) -> dict:
        return {}
    
    @property
    def log_level(self) -> str:
        return "warning"


class MissingSubjectError(AccessError):
    pass


class InvalidSubjectError(AccessError):
    pass


class UserNotFoundError(AccessError):
    pass


class InvalidGroupIdError(AccessError):
    pass


class GroupNotFoundError(AccessError):
    pass


class NotGroupMemberError(AccessError):
    pass


class MissingPermissionsError(AccessError):
    def __init__(self, missing_permissions: list[str], *, require_all: bool):
        self.missing_permissions = missing_permissions
        self.require_all = require_all
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "missing_permissions": self.missing_permissions,
            "require_all": self.require_all,
        }
