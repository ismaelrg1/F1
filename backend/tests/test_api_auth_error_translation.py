from app.api.error_catalogs.auth import AUTH_ERROR_MAP
from app.api.error_translators import translate_domain_error
from app.domain.auth.errors import (
    GoogleAccountNotRegisteredError,
    GoogleEmailNotVerifiedError,
    InvalidAccessTokenError,
    InactiveUserError,
    InvalidGoogleTokenError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
    MissingAccessTokenError,
    MissingRefreshTokenError,
    MissingRefreshSubjectError,
    UserAlreadyExistsError,
)


def test_translate_auth_invalid_credentials_returns_safe_message() -> None:
    http_exc = translate_domain_error(
        InvalidCredentialsError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 401
    assert http_exc.detail["error"]["code"] == "auth.invalid_credentials"
    assert http_exc.detail["error"]["message"] == "Invalid credentials"


def test_translate_auth_inactive_user_returns_forbidden() -> None:
    http_exc = translate_domain_error(
        InactiveUserError(),
        error_map=AUTH_ERROR_MAP,
        locale="es",
    )

    assert http_exc.status_code == 403
    assert http_exc.detail["error"]["code"] == "auth.inactive_user"
    assert http_exc.detail["error"]["message"] == "Esta cuenta no puede usar inicio de sesion por contrasena"


def test_translate_auth_missing_refresh_subject_returns_unauthorized() -> None:
    http_exc = translate_domain_error(
        MissingRefreshSubjectError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 401
    assert http_exc.detail["error"]["code"] == "auth.missing_refresh_subject"


def test_translate_auth_missing_access_token_returns_unauthorized() -> None:
    http_exc = translate_domain_error(
        MissingAccessTokenError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 401
    assert http_exc.detail["error"]["code"] == "auth.missing_access_token"


def test_translate_auth_invalid_access_token_returns_unauthorized() -> None:
    http_exc = translate_domain_error(
        InvalidAccessTokenError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 401
    assert http_exc.detail["error"]["code"] == "auth.invalid_access_token"


def test_translate_auth_missing_refresh_token_returns_unauthorized() -> None:
    http_exc = translate_domain_error(
        MissingRefreshTokenError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 401
    assert http_exc.detail["error"]["code"] == "auth.missing_refresh_token"


def test_translate_auth_invalid_refresh_token_returns_unauthorized() -> None:
    http_exc = translate_domain_error(
        InvalidRefreshTokenError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 401
    assert http_exc.detail["error"]["code"] == "auth.invalid_refresh_token"


def test_translate_auth_user_already_exists_returns_conflict() -> None:
    http_exc = translate_domain_error(
        UserAlreadyExistsError(field="email"),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 409
    assert http_exc.detail["error"]["code"] == "auth.user_already_exists"
    assert http_exc.detail["error"]["message"] == "A user with this data already exists"


def test_translate_auth_invalid_google_token_returns_unauthorized() -> None:
    http_exc = translate_domain_error(
        InvalidGoogleTokenError(),
        error_map=AUTH_ERROR_MAP,
        locale="es",
    )

    assert http_exc.status_code == 401
    assert http_exc.detail["error"]["code"] == "auth.invalid_google_token"


def test_translate_auth_google_email_not_verified_returns_forbidden() -> None:
    http_exc = translate_domain_error(
        GoogleEmailNotVerifiedError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 403
    assert http_exc.detail["error"]["code"] == "auth.google_email_not_verified"


def test_translate_auth_google_account_not_registered_returns_not_found() -> None:
    http_exc = translate_domain_error(
        GoogleAccountNotRegisteredError(),
        error_map=AUTH_ERROR_MAP,
        locale="en",
    )

    assert http_exc.status_code == 404
    assert http_exc.detail["error"]["code"] == "auth.google_account_not_registered"


def test_translate_auth_invalid_password_reset_token_returns_bad_request() -> None:
    http_exc = translate_domain_error(
        InvalidPasswordResetTokenError(reason="expired"),
        error_map=AUTH_ERROR_MAP,
        locale="es",
    )

    assert http_exc.status_code == 400
    assert http_exc.detail["error"]["code"] == "auth.invalid_password_reset_token"
    assert http_exc.detail["error"]["message"] == "El token de restablecimiento no es valido o ha expirado"
