from fastapi import status

from app.api.error_catalogs.base import ErrorCatalogEntry
from app.domain.management.scoring import (
    ScoringBetContextNotFoundError,
    ScoringEvaluatorNotFoundError,
    ScoringOfficialResultsRequiredError,
)

SCORING_ERROR_MAP = {
    ScoringBetContextNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="management.scoring.bet_context_not_found",
    ),
    ScoringOfficialResultsRequiredError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="management.scoring.official_results_required",
    ),
    ScoringEvaluatorNotFoundError: ErrorCatalogEntry(
        status_code=status.HTTP_409_CONFLICT,
        error_code="management.scoring.evaluator_not_found",
    ),
}