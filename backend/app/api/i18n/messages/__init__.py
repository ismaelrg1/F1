from app.api.i18n.messages.access import MESSAGES_ACCESS
from app.api.i18n.messages.admin import MESSAGES_ADMIN
from app.api.i18n.messages.auth import MESSAGES_AUTH
from app.api.i18n.messages.bets import MESSAGES_BETS
from app.api.i18n.messages.errors import MESSAGES_ERRORS
from app.api.i18n.messages.ranking import MESSAGES_RANKING

DEFAULT_LOCALE = "en"

MESSAGES = {
    "en": {
        **MESSAGES_ACCESS["en"],
        **MESSAGES_AUTH["en"],
        **MESSAGES_ADMIN["en"],
        **MESSAGES_BETS["en"],
        **MESSAGES_ERRORS["en"],
        **MESSAGES_RANKING["en"],
    },
    "es": {
        **MESSAGES_ACCESS["es"],
        **MESSAGES_AUTH["es"],
        **MESSAGES_ADMIN["es"],
        **MESSAGES_BETS["es"],
        **MESSAGES_ERRORS["es"],
        **MESSAGES_RANKING["es"]
    },
}


def resolve_message(error_code: str, locale: str | None) -> str:
    normalized_locale = (locale or DEFAULT_LOCALE).split(",")[0].split("-")[0].lower()
    messages = MESSAGES.get(normalized_locale) or MESSAGES[DEFAULT_LOCALE]
    return messages.get(error_code) or MESSAGES[DEFAULT_LOCALE].get(error_code, error_code)


def render_message(error_code: str, locale: str | None, public_params: dict | None = None) -> str:
    template = resolve_message(error_code, locale)
    if not public_params:
        return template

    try:
        return template.format(**public_params)
    except KeyError:
        return template


__all__ = ["DEFAULT_LOCALE", "MESSAGES", "render_message", "resolve_message"]