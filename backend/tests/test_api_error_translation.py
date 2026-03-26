from app.api.error_catalogs import ACCESS_ERROR_MAP
from app.api.error_translators import get_preferred_locale, translate_domain_error
from app.domain.access.errors import GroupNotFoundError, MissingPermissionsError


def test_translate_access_error_returns_error_code_and_english_message() -> None:
    exc = GroupNotFoundError()

    http_exc = translate_domain_error(exc, error_map=ACCESS_ERROR_MAP, locale="en")

    assert http_exc.status_code == 404
    assert http_exc.detail["error"]["code"] == "access.group_not_found"
    assert http_exc.detail["error"]["message"] == "Group not found"


def test_translate_access_error_returns_spanish_message() -> None:
    exc = GroupNotFoundError()

    http_exc = translate_domain_error(exc, error_map=ACCESS_ERROR_MAP, locale="es")

    assert http_exc.status_code == 404
    assert http_exc.detail["error"]["message"] == "Grupo no encontrado"


def test_translate_access_error_hides_dynamic_domain_details_from_client() -> None:
    exc = MissingPermissionsError(["RESULTS_PUBLISH", "RESULTS_EDIT"], require_all=True)

    http_exc = translate_domain_error(exc, error_map=ACCESS_ERROR_MAP, locale="en")

    assert http_exc.status_code == 403
    assert http_exc.detail["error"]["code"] == "access.missing_permissions"
    assert http_exc.detail["error"]["message"] == "You are not authorized to perform this action"
    assert "RESULTS_PUBLISH" not in str(http_exc.detail)


def test_translate_unknown_domain_error_falls_back_to_generic_500() -> None:
    class UnknownAccessError(Exception):
        pass

    http_exc = translate_domain_error(UnknownAccessError(), error_map=ACCESS_ERROR_MAP, locale="en")

    assert http_exc.status_code == 500
    assert http_exc.detail["error"]["code"] == "errors.unhandled"


def test_get_preferred_locale_uses_accept_language_first_value() -> None:
    locale = get_preferred_locale("es-ES,es;q=0.9,en;q=0.8")

    assert locale == "es-ES"
