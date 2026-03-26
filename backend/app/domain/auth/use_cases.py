from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from app.domain.auth.errors import (
    GoogleAccountNotRegisteredError,
    GoogleEmailNotVerifiedError,
    InvalidGoogleTokenError,
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    PasswordResetNotAvailableError,
    PasswordResetTooManyRequestsError,
    InvalidPasswordResetTokenError
)
from app.domain.auth.models import AuthenticatedLoginUser
from app.domain.auth.ports import (
    AuthRepository, 
    GoogleIdentityVerifier, 
    PasswordHasher,
    PasswordResetTokenRepository,
    ResetTokenHasher,
    EmailSender,
)

class LoginLocalUser:
    def __init__(self, repository: AuthRepository, password_hasher: PasswordHasher):
        self._repository = repository
        self._password_hasher = password_hasher

    def execute(self, username: str, password: str) -> AuthenticatedLoginUser:
        user = self._repository.get_by_username(username)
        if user is None:
            raise InvalidCredentialsError()
        if user.password_hash is None or user.auth_provider != "LOCAL":
            raise InactiveUserError()
        if not self._password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError()
        return user


class RegisterLocalUser:
    def __init__(self, repository: AuthRepository, password_hasher: PasswordHasher):
        self._repository = repository
        self._password_hasher = password_hasher

    def execute(self, *, username: str, email: str, password: str) -> AuthenticatedLoginUser:
        if self._repository.get_by_username(username) is not None:
            raise UserAlreadyExistsError(field="username")
        if self._repository.get_by_email(email) is not None:
            raise UserAlreadyExistsError(field="email")

        password_hash = self._password_hasher.hash(password)
        return self._repository.create_local_user(
            username=username,
            email=email,
            password_hash=password_hash,
        )


class _GoogleIdentityMixin:
    def _verify_identity(self, id_token: str):
        try:
            identity = self._verifier.verify(id_token)
        except InvalidGoogleTokenError:
            raise
        except Exception as exc:
            raise InvalidGoogleTokenError() from exc

        if not identity.email_verified:
            raise GoogleEmailNotVerifiedError()
        return identity


class LoginGoogleUser(_GoogleIdentityMixin):
    def __init__(self, repository: AuthRepository, verifier: GoogleIdentityVerifier):
        self._repository = repository
        self._verifier = verifier

    def execute(self, id_token: str) -> AuthenticatedLoginUser:
        identity = self._verify_identity(id_token)
        user = self._repository.get_by_google_sub(identity.sub)
        if user is None:
            raise GoogleAccountNotRegisteredError()
        return user


class RegisterGoogleUser(_GoogleIdentityMixin):
    def __init__(self, repository: AuthRepository, verifier: GoogleIdentityVerifier):
        self._repository = repository
        self._verifier = verifier

    def execute(self, id_token: str) -> AuthenticatedLoginUser:
        identity = self._verify_identity(id_token)

        existing_by_sub = self._repository.get_by_google_sub(identity.sub)
        if existing_by_sub is not None:
            raise UserAlreadyExistsError(field="google_sub")

        existing_by_email = self._repository.get_by_email(identity.email)
        if existing_by_email is not None:
            raise UserAlreadyExistsError(field="email")

        username = self._build_unique_username(identity.email)
        return self._repository.create_google_user(
            username=username,
            email=identity.email,
            google_sub=identity.sub,
        )

    def _build_unique_username(self, email: str) -> str:
        base = email.split("@", 1)[0].strip().lower() or "google_user"
        candidate = base[:50]
        suffix = 1

        while self._repository.get_by_username(candidate) is not None:
            suffix_str = str(suffix)
            candidate = f"{base[: max(1, 50 - len(suffix_str) - 1)]}_{suffix_str}"
            suffix += 1

        return candidate


LoginUser = LoginLocalUser


class RequestPasswordReset:
    def __init__(
            self,
            auth_repository: AuthRepository,
            token_repository: PasswordResetTokenRepository,
            token_hasher: ResetTokenHasher,
            email_sender: EmailSender,
            *,
            reset_base_url: str,
            token_ttl: timedelta, 
            request_cooldown: timedelta
    ) -> None:
        
        self._auth_repository = auth_repository
        self._token_repository = token_repository
        self._token_hasher = token_hasher
        self._email_sender = email_sender
        self._reset_base_url = reset_base_url
        self._token_ttl = token_ttl
        self._request_cooldown = request_cooldown

    def execute(self, email: str) -> None:
        user = self._auth_repository.get_by_email(email)

        if user is None:
            return
        
        if user.auth_provider != "LOCAL":
            raise PasswordResetNotAvailableError(provider=user.auth_provider)
        
        active_token = self._token_repository.get_active_for_user(user.id)
        now = datetime.now(UTC)

        if active_token and (now - active_token.created_at).total_seconds() < self._request_cooldown.total_seconds():
            raise PasswordResetTooManyRequestsError(
                cooldown_seconds=int(self._request_cooldown.total_seconds())
            )
        
        self._token_repository.invalidate_active_for_user(
            user.id,
            invalidated_at=now,
        )

        raw_token = token_urlsafe(32)
        token_hash = self._token_hasher.hash(raw_token)
        expires_at = now + self._token_ttl

        self._token_repository.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        reset_url = f"{self._reset_base_url}?token={raw_token}"
        self._email_sender.send_password_reset_email(
            to_email=user.email,
            reset_url=reset_url,
        )

class ResetPassword:
    def __init__(
        self,
        auth_repository: AuthRepository,
        token_repository: PasswordResetTokenRepository,
        token_hasher: ResetTokenHasher,
        password_hasher: PasswordHasher,
    ) -> None:
        self._auth_repository = auth_repository
        self._token_repository = token_repository
        self._token_hasher = token_hasher
        self._password_hasher = password_hasher

    def execute(self, *, token: str, new_password: str) -> None:
        token_hash = self._token_hasher.hash(token)
        token_record = self._token_repository.get_by_token_hash(token_hash)
        now = datetime.now(UTC)

        if token_record is None:
            raise InvalidPasswordResetTokenError(reason="not_found")

        if token_record.used_at is not None:
            raise InvalidPasswordResetTokenError(reason="used")

        if token_record.invalidated_at is not None:
            raise InvalidPasswordResetTokenError(reason="invalidated")

        if token_record.expires_at <= now:
            raise InvalidPasswordResetTokenError(reason="expired")

        user = self._auth_repository.get_by_id(token_record.user_id)
        if user is None:
            raise InvalidPasswordResetTokenError(reason="user_not_found")
        
        if user.auth_provider != "LOCAL":
            raise InvalidPasswordResetTokenError(reason="provider_not_local")

        password_hash = self._password_hasher.hash(new_password)

        self._auth_repository.update_password(
            user_id=user.id,
            password_hash=password_hash,
        )
        self._token_repository.mark_as_used(token_hash, used_at=now)
