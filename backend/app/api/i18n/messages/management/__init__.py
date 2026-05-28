from app.api.i18n.messages.management.group import MESSAGES_MANAGEMENT_GROUP
from app.api.i18n.messages.management.official_results import MESSAGES_OFFICIAL_RESULTS
from app.api.i18n.messages.management.result_publications import MESSAGES_RESULT_PUBLICATIONS
from app.api.i18n.messages.management.scoring import MESSAGES_SCORING

MESSAGES_MANAGEMENT = {
    "en": {
        **MESSAGES_MANAGEMENT_GROUP["en"],
        **MESSAGES_OFFICIAL_RESULTS["en"],
        **MESSAGES_RESULT_PUBLICATIONS["en"],
        **MESSAGES_SCORING["en"],
    },
    "es": {
        **MESSAGES_MANAGEMENT_GROUP["es"],
        **MESSAGES_OFFICIAL_RESULTS["es"],
        **MESSAGES_RESULT_PUBLICATIONS["es"],
        **MESSAGES_SCORING["es"]
    },
}

__all__ = ["MESSAGES_MANAGEMENT"]
