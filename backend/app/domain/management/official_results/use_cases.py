from uuid import UUID

from app.db.scoring.official_result import SourceType
from app.domain.management.official_results.errors import (
    OfficialResultsAlreadyExistsError,
    OfficialResultsBetContextNotFoundError,
    OfficialResultsBetScoreNotFoundError,
    OfficialResultsEventSessionNotFoundError,
    OfficialResultsInvalidScopeError,
    OfficialResultsNotFoundError,
    OfficialResultsTestingEventSessionNotFoundError,
)
from app.domain.management.official_results.models import (
    OfficialResult,
    OfficialResultInput,
)
from app.domain.management.official_results.ports import OfficialResultRepository


class CreateOfficialResults:
    def __init__(self, repository: OfficialResultRepository):
        self._repository = repository

    def execute(
        self,
        *,
        bet_context_public_id: UUID,
        event_session_public_id: UUID | None,
        testing_event_session_public_id: UUID | None,
        source: SourceType,
        results: list[OfficialResultInput],
    ) -> list[OfficialResult]:
        bet_context_id, _ = self._resolve_scope_ids(
            bet_context_public_id=bet_context_public_id,
            event_session_public_id=event_session_public_id,
            testing_event_session_public_id=testing_event_session_public_id,
        )

        event_session_id, testing_event_session_id = self._resolve_session_scope(
            bet_context_id=bet_context_id,
            event_session_public_id=event_session_public_id,
            testing_event_session_public_id=testing_event_session_public_id,
        )

        received_codes = {item.bet_score_code.strip() for item in results}
        score_ids_by_code = self._repository.get_bet_score_ids_by_codes(codes=received_codes)
        if set(score_ids_by_code) != received_codes:
            raise OfficialResultsBetScoreNotFoundError()

        if self._repository.official_results_exist_for_scope(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
            bet_score_ids=set(score_ids_by_code.values()),
        ):
            raise OfficialResultsAlreadyExistsError()

        normalized_results = [
            OfficialResultInput(
                bet_score_code=item.bet_score_code.strip(),
                value=item.value.strip(),
            )
            for item in results
        ]

        return self._repository.create_official_results(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
            source=source,
            results=normalized_results,
            score_ids_by_code=score_ids_by_code,
        )

    def _resolve_scope_ids(
        self,
        *,
        bet_context_public_id: UUID,
        event_session_public_id: UUID | None,
        testing_event_session_public_id: UUID | None,
    ) -> tuple[int, UUID]:
        if event_session_public_id is not None and testing_event_session_public_id is not None:
            raise OfficialResultsInvalidScopeError()

        try:
            return self._repository.get_bet_context_scope(
                bet_context_public_id=bet_context_public_id,
            )
        except Exception as exc:
            raise OfficialResultsBetContextNotFoundError() from exc

    def _resolve_session_scope(
        self,
        *,
        bet_context_id: int,
        event_session_public_id: UUID | None,
        testing_event_session_public_id: UUID | None,
    ) -> tuple[int | None, int | None]:
        if event_session_public_id is not None:
            session = self._repository.get_event_session_scope(
                bet_context_id=bet_context_id,
                event_session_public_id=event_session_public_id,
            )
            if session is None:
                raise OfficialResultsEventSessionNotFoundError()
            return session[0], None

        if testing_event_session_public_id is not None:
            session = self._repository.get_testing_event_session_scope(
                bet_context_id=bet_context_id,
                testing_event_session_public_id=testing_event_session_public_id,
            )
            if session is None:
                raise OfficialResultsTestingEventSessionNotFoundError()
            return None, session[0]

        return None, None


class UpdateOfficialResults:
    def __init__(self, repository: OfficialResultRepository):
        self._repository = repository

    def execute(
        self,
        *,
        bet_context_public_id: UUID,
        event_session_public_id: UUID | None,
        testing_event_session_public_id: UUID | None,
        source: SourceType,
        results: list[OfficialResultInput],
    ) -> list[OfficialResult]:
        creator = CreateOfficialResults(self._repository)

        bet_context_id, _ = creator._resolve_scope_ids(
            bet_context_public_id=bet_context_public_id,
            event_session_public_id=event_session_public_id,
            testing_event_session_public_id=testing_event_session_public_id,
        )

        event_session_id, testing_event_session_id = creator._resolve_session_scope(
            bet_context_id=bet_context_id,
            event_session_public_id=event_session_public_id,
            testing_event_session_public_id=testing_event_session_public_id,
        )

        received_codes = {item.bet_score_code.strip() for item in results}
        score_ids_by_code = self._repository.get_bet_score_ids_by_codes(codes=received_codes)
        if set(score_ids_by_code) != received_codes:
            raise OfficialResultsBetScoreNotFoundError()

        if self._repository.official_results_missing_for_scope(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
            bet_score_ids=set(score_ids_by_code.values()),
        ):
            raise OfficialResultsNotFoundError()

        normalized_results = [
            OfficialResultInput(
                bet_score_code=item.bet_score_code.strip(),
                value=item.value.strip(),
            )
            for item in results
        ]

        return self._repository.update_official_results(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
            source=source,
            results=normalized_results,
            score_ids_by_code=score_ids_by_code,
        )