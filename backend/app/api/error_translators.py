import logging
from collections.abc import Mapping

from fastapi import HTTPException, status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.api.i18n import DEFAULT_LOCALE, render_message

logger = logging.getLogger(__name__)

LOG_METHODS = {
    "debug": logger.debug,
    "info": logger.info,
    "warning": logger.warning,
    "error": logger.error,
    "critical": logger.critical,
}

def get_preferred_locale(accept_language: str | None) -> str:
    if not accept_language:
        return DEFAULT_LOCALE
    return accept_language.split(",")[0].strip()


def translate_domain_error(
    exc: Exception,
    *,
    error_map: Mapping[type[Exception], ErrorCatalogEntry],
    locale: str | None,
) -> HTTPException:
    error_type = type(exc)
    entry = error_map.get(error_type)
    error_context = getattr(exc, "context", {})
    public_params = getattr(exc, "public_params", {})

    log_level = getattr(exc, "log_level", "warning")
    log_method = LOG_METHODS.get(log_level, logger.warning)

    if entry is None:
        logger.exception(
            "Unhandled domain error",
            extra={
                "error_type": error_type.__name__,
                "error_context": error_context,
            },
        )
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "errors.unhandled",
                    "message": render_message("errors.unhandled", locale),
                }
            },
        )

    log_method(
        "Translated domain error",
        extra={
            "error_type": error_type.__name__,
            "error_code": entry.error_code,
            "error_context": error_context,
        },
    )

    return HTTPException(
        status_code=entry.status_code,
        detail={
            "error": {
                "code": entry.error_code,
                "message": render_message(entry.error_code, locale, public_params),
            }
        },
    )
