from app.domain.admin.bet_contexts.errors import (
    BetContextGenerationGroupNotFoundError,
    BetContextGenerationSeasonNotFoundError,
)
from app.domain.admin.bet_contexts.models import AdminBetContextGenerationResult
from app.domain.admin.bet_contexts.ports import AdminBetContextRepository


class GenerateBetContexts:
    def __init__(self, repository: AdminBetContextRepository):
        self._repository = repository

    def execute(
        self,
        *,
        season_id: int,
        group_id: int | None,
        include_season: bool,
        include_race_events: bool,
        include_testing_events: bool,
    ) -> AdminBetContextGenerationResult:
        if not self._repository.season_exists(season_id=season_id):
            raise BetContextGenerationSeasonNotFoundError(season_id=season_id)

        if group_id is not None and not self._repository.group_exists(group_id=group_id):
            raise BetContextGenerationGroupNotFoundError(group_id=group_id)

        group_ids = self._repository.list_group_ids(group_id=group_id)
        race_events = (
            self._repository.list_race_events_for_season(season_id=season_id)
            if include_race_events
            else []
        )
        testing_events = (
            self._repository.list_testing_events_for_season(season_id=season_id)
            if include_testing_events
            else []
        )

        created = 0
        existing = 0
        season_contexts_created = 0
        race_event_contexts_created = 0
        testing_event_contexts_created = 0

        for current_group_id in group_ids:
            if include_season:
                was_created = self._repository.ensure_season_context(
                    group_id=current_group_id,
                    season_id=season_id,
                    label=f"Season {season_id}",
                )

                if was_created:
                    created += 1
                    season_contexts_created += 1
                else:
                    existing += 1

            for race_event in race_events:
                was_created = self._repository.ensure_race_event_context(
                    group_id=current_group_id,
                    season_id=season_id,
                    race_event_id=race_event.id,
                    label=race_event.name,
                )

                if was_created:
                    created += 1
                    race_event_contexts_created += 1
                else:
                    existing += 1

            for testing_event in testing_events:
                was_created = self._repository.ensure_testing_event_context(
                    group_id=current_group_id,
                    season_id=season_id,
                    testing_event_id=testing_event.id,
                    label=testing_event.name,
                )

                if was_created:
                    created += 1
                    testing_event_contexts_created += 1
                else:
                    existing += 1

        return AdminBetContextGenerationResult(
            groups_processed=len(group_ids),
            created=created,
            existing=existing,
            season_contexts_created=season_contexts_created,
            race_event_contexts_created=race_event_contexts_created,
            testing_event_contexts_created=testing_event_contexts_created,
        )