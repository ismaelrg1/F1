from uuid import UUID

from app.domain.management.result_publications.errors import (
    ResultPublicationAlreadyExistsError,
    ResultPublicationBetContextNotFoundError,
    ResultPublicationEventSessionNotFoundError,
    ResultPublicationNotFoundError,
    ResultPublicationOfficialResultsNotFoundError,
    ResultPublicationTestingEventSessionNotFoundError,
    ResultPublicationScoringRequiredError,
)
from app.domain.management.result_publications.models import ResultPublicationResult
from app.domain.management.result_publications.ports import ResultPublicationRepository


class PublishRaceEventResults:
    def __init__(self, repository: ResultPublicationRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
        event_session_public_id: UUID | None,
        published_by_user_id: int,
        note: str | None,
    ):
        bet_context_id = self._repository.get_race_bet_context_id(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
        )
        if bet_context_id is None:
            raise ResultPublicationBetContextNotFoundError()

        event_session_id = None
        if event_session_public_id is not None:
            event_session_id = self._repository.get_event_session_id(
                bet_context_id=bet_context_id,
                event_session_public_id=event_session_public_id,
            )
            if event_session_id is None:
                raise ResultPublicationEventSessionNotFoundError()

        if event_session_id is None:
            has_official_results = self._repository.official_results_exist(
                bet_context_id=bet_context_id,
                event_session_id=None,
                testing_event_session_id=None,
            )
            has_calculated_scores = self._repository.has_calculated_scores(
                bet_context_id=bet_context_id,
                event_session_id=None,
                testing_event_session_id=None,
            )
            if not has_official_results and not has_calculated_scores:
                return ResultPublicationResult(
                    race_event_public_id=race_event_public_id,
                    event_session_public_id=None,
                    testing_event_public_id=None,
                    testing_event_session_public_id=None,
                    season_year=None,
                    published_at=None,
                    note=note,
                    published=False,
                    reason="no_context_scores",
                )

        return _publish(
            repository=self._repository,
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=None,
            published_by_user_id=published_by_user_id,
            note=note,
        )


class UnpublishRaceEventResults:
    def __init__(self, repository: ResultPublicationRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
        event_session_public_id: UUID | None,
    ) -> None:
        bet_context_id = self._repository.get_race_bet_context_id(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
        )
        if bet_context_id is None:
            raise ResultPublicationBetContextNotFoundError()

        event_session_id = None
        if event_session_public_id is not None:
            event_session_id = self._repository.get_event_session_id(
                bet_context_id=bet_context_id,
                event_session_public_id=event_session_public_id,
            )
            if event_session_id is None:
                raise ResultPublicationEventSessionNotFoundError()

        _unpublish(
            repository=self._repository,
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=None,
        )


class PublishTestingEventResults:
    def __init__(self, repository: ResultPublicationRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
        testing_event_session_public_id: UUID | None,
        published_by_user_id: int,
        note: str | None,
    ):
        bet_context_id = self._repository.get_testing_bet_context_id(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
        )
        if bet_context_id is None:
            raise ResultPublicationBetContextNotFoundError()

        testing_event_session_id = None
        if testing_event_session_public_id is not None:
            testing_event_session_id = self._repository.get_testing_event_session_id(
                bet_context_id=bet_context_id,
                testing_event_session_public_id=testing_event_session_public_id,
            )
            if testing_event_session_id is None:
                raise ResultPublicationTestingEventSessionNotFoundError()

        return _publish(
            repository=self._repository,
            bet_context_id=bet_context_id,
            event_session_id=None,
            testing_event_session_id=testing_event_session_id,
            published_by_user_id=published_by_user_id,
            note=note,
        )


class UnpublishTestingEventResults:
    def __init__(self, repository: ResultPublicationRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
        testing_event_session_public_id: UUID | None,
    ) -> None:
        bet_context_id = self._repository.get_testing_bet_context_id(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
        )
        if bet_context_id is None:
            raise ResultPublicationBetContextNotFoundError()

        testing_event_session_id = None
        if testing_event_session_public_id is not None:
            testing_event_session_id = self._repository.get_testing_event_session_id(
                bet_context_id=bet_context_id,
                testing_event_session_public_id=testing_event_session_public_id,
            )
            if testing_event_session_id is None:
                raise ResultPublicationTestingEventSessionNotFoundError()

        _unpublish(
            repository=self._repository,
            bet_context_id=bet_context_id,
            event_session_id=None,
            testing_event_session_id=testing_event_session_id,
        )


class PublishSeasonResults:
    def __init__(self, repository: ResultPublicationRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        season_year: int,
        published_by_user_id: int,
        note: str | None,
    ):
        bet_context_id = self._repository.get_season_bet_context_id(
            group_id=group_id,
            season_year=season_year,
        )
        if bet_context_id is None:
            raise ResultPublicationBetContextNotFoundError()

        return _publish(
            repository=self._repository,
            bet_context_id=bet_context_id,
            event_session_id=None,
            testing_event_session_id=None,
            published_by_user_id=published_by_user_id,
            note=note,
        )


class UnpublishSeasonResults:
    def __init__(self, repository: ResultPublicationRepository):
        self._repository = repository

    def execute(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> None:
        bet_context_id = self._repository.get_season_bet_context_id(
            group_id=group_id,
            season_year=season_year,
        )
        if bet_context_id is None:
            raise ResultPublicationBetContextNotFoundError()

        _unpublish(
            repository=self._repository,
            bet_context_id=bet_context_id,
            event_session_id=None,
            testing_event_session_id=None,
        )


def _publish(
    *,
    repository: ResultPublicationRepository,
    bet_context_id: int,
    event_session_id: int | None,
    testing_event_session_id: int | None,
    published_by_user_id: int,
    note: str | None,
):
    has_official_results = repository.official_results_exist(
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
    )
    has_calculated_scores = repository.has_calculated_scores(
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
    )

    if not has_official_results and not has_calculated_scores:
        raise ResultPublicationOfficialResultsNotFoundError()

    if repository.publication_exists(
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
    ):
        raise ResultPublicationAlreadyExistsError()

    if not has_calculated_scores:
        raise ResultPublicationScoringRequiredError()

    result = repository.create_publication(
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
        published_by_user_id=published_by_user_id,
        note=note,
    )

    repository.recalculate_season_aggregates_for_bet_context(
        bet_context_id=bet_context_id,
    )

    return result


def _unpublish(
    *,
    repository: ResultPublicationRepository,
    bet_context_id: int,
    event_session_id: int | None,
    testing_event_session_id: int | None,
) -> None:
    if not repository.publication_exists(
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
    ):
        raise ResultPublicationNotFoundError()

    repository.delete_publication(
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
    )

    repository.recalculate_season_aggregates_for_bet_context(
        bet_context_id=bet_context_id,
    )
