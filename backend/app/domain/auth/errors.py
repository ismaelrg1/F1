class AuthError(Exception):
    @property
    def context(self) -> dict:
        return {}

    @property
    def public_params(self) -> dict:
        return {}

    @property
    def log_level(self) -> str:
        return "warning"


class InvalidCredentialsError(AuthError):
    pass


class InactiveUserError(AuthError):
    pass


class MissingRefreshSubjectError(AuthError):
    pass


class UserAlreadyExistsError(AuthError):
    def __init__(self, *, field: str):
        self.field = field
        super().__init__()

    @property
    def context(self) -> dict:
        return {"field": self.field}


class InvalidGoogleTokenError(AuthError):
    pass


class GoogleEmailNotVerifiedError(AuthError):
    pass


class GoogleAccountNotRegisteredError(AuthError):
    pass


class MissingAccessTokenError(AuthError):
    pass


class InvalidAccessTokenError(AuthError):
    pass


class MissingRefreshTokenError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass

class PasswordResetError(AuthError):
    pass

class PasswordResetNotAvailableError(PasswordResetError):
    def __init__(self, *, provider: str):
        self.provider = provider
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "provider": self.provider,
        }


class PasswordResetTooManyRequestsError(PasswordResetError):
    def __init__(self, *, cooldown_seconds: int):
        self.cooldown_seconds = cooldown_seconds
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "cooldown_seconds": self.cooldown_seconds,
        }
    
class InvalidPasswordResetTokenError(PasswordResetError):
    def __init__(self, *, reason: str):
        self.reason = reason
        super().__init__()

    @property
    def context(self) -> dict:
        return {
            "reason": self.reason,
        }


