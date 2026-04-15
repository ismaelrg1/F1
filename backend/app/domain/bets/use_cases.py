from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.betting import BetException, BetTemplateItem
from app.db.competition import DriverEntry, EventSession, RaceEvent, TestingEvent, TestingEventSession
from app.db.enums import BetValueType, SessionType
from app.domain.bets.errors import (
    BetContextNotFoundForRaceEventError,
    RaceEventNotFoundForBetQuestionsError,
)

from app.domain.bets.models import (
    BetQuestionOptionResult,
    BetQuestionResult,
    RaceEventBetQuestionsSessionResult,
    RaceEventBetQuestionsResult,
    TestingEventBetQuestionsSessionResult,
    TestingEventBetQuestionsResult,
)

from app.domain.bets.ports import BetQuestionsRepository

class GetRaceEventBetQuestions:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(self, *, race_event_public_id: UUID, group_id: int) -> RaceEventBetQuestionsResult:
        race_event = self._repository.get_race_event_by_public_id(race_event_public_id)
        if race_event is None:
            raise RaceEventNotFoundForBetQuestionsError()

        bet_context = self._repository.get_gp_bet_context(
            group_id=group_id,
            race_event_id=race_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForRaceEventError()

        templates = self._repository.list_gp_templates_for_season(season_id=race_event.season_id)

        event_template = None
        session_templates: dict[SessionType, object] = {}
        for template in templates:
            if template.scope.value == "EVENT":
                event_template = template
            else:
                session_templates[template.session_type] = template

        event_exceptions = {
            exception.bet_score_id: exception
            for exception in bet_context.bet_exceptions
            if exception.event_session_id is None
        }

        session_exceptions = {
            (exception.event_session_id, exception.bet_score_id): exception
            for exception in bet_context.bet_exceptions
            if exception.event_session_id is not None
        }

        event_questions = []
        if event_template is not None:
            event_questions = self._build_race_questions(
                race_event=race_event,
                event_session=None,
                items=event_template.items,
                fallback_exceptions=event_exceptions,
                specific_exceptions=None,
            )

        sessions = []
        for session in sorted(
            race_event.event_sessions,
            key=lambda s: (s.scheduled_start_datetime or s.start_datetime, s.id),
        ):
            template = session_templates.get(session.session_type)
            if template is None:
                continue

            specific = {
                bet_score_id: exception
                for (event_session_id, bet_score_id), exception in session_exceptions.items()
                if event_session_id == session.id
            }

            questions = self._build_race_questions(
                race_event=race_event,
                event_session=session,
                items=template.items,
                fallback_exceptions=event_exceptions,
                specific_exceptions=specific,
            )

            sessions.append(
                RaceEventBetQuestionsSessionResult(
                    event_session_public_id=session.public_id,
                    session_type=session.session_type,
                    start_datetime=session.start_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    lock_cutoff=session.lock_cutoff,
                    scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                    status=session.status,
                    questions=questions,
                )
            )

        return RaceEventBetQuestionsResult(
            bet_context_public_id=bet_context.public_id,
            kind=bet_context.kind,
            race_event_public_id=race_event.public_id,
            label=bet_context.label,
            event_questions=event_questions,
            sessions=sessions,
        )

    def _build_race_questions(
        self,
        *,
        race_event: RaceEvent,
        event_session: EventSession | None,
        items: list[BetTemplateItem],
        fallback_exceptions: dict[int, BetException],
        specific_exceptions: dict[int, BetException] | None,
    ) -> list[BetQuestionResult]:
        questions: list[BetQuestionResult] = []

        for item in sorted(items, key=lambda i: (i.display_order, i.id)):
            bet_score = item.bet_score

            exception = None
            if specific_exceptions is not None:
                exception = specific_exceptions.get(bet_score.id)
            if exception is None:
                exception = fallback_exceptions.get(bet_score.id)

            if exception is not None and exception.is_disabled is True:
                continue

            base_points = bet_score.base_points
            constraints_json = bet_score.constraints_json

            if exception is not None and exception.override_points is not None:
                base_points = exception.override_points

            if exception is not None and exception.override_constraints_json is not None:
                constraints_json = exception.override_constraints_json

            constraints_json = self._build_race_constraints(
                race_event=race_event,
                event_session=event_session,
                value_type=bet_score.value_type,
                constraints_json=constraints_json,
            )

            questions.append(
                BetQuestionResult(
                    code=bet_score.code,
                    label=bet_score.label,
                    value_type=bet_score.value_type.value,
                    required=item.required,
                    display_order=item.display_order,
                    base_points=base_points,
                    constraints_json=constraints_json,
                    options=self._build_race_options(
                        race_event=race_event,
                        event_session=event_session,
                        value_type=bet_score.value_type,
                    ),
                )
            )

        return questions

    def _build_race_options(
        self,
        *,
        race_event: RaceEvent,
        event_session: EventSession | None,
        value_type: BetValueType,
    ) -> list[BetQuestionOptionResult] | None:
        if value_type in {BetValueType.DRIVER, BetValueType.TEAM, BetValueType.ENGINE, BetValueType.POSITION}:
            roster = self._resolve_race_roster(
                race_event=race_event,
                event_session=event_session,
            )
            driver_numbers_by_driver_id = {
                season_driver.driver_id: season_driver.driver_number
                for season_driver in race_event.season.season_drivers
            }

        if value_type == BetValueType.DRIVER:
            seen: set[str] = set()
            options: list[BetQuestionOptionResult] = []
            for entry in roster:
                if entry.driver.code in seen:
                    continue
                seen.add(entry.driver.code)
                options.append(
                    BetQuestionOptionResult(
                        value=entry.driver.code,
                        label=entry.driver.name,
                        meta={
                            "code": entry.driver.code,
                            "driver_number": driver_numbers_by_driver_id.get(entry.driver_id),
                        },
                    )
                )
            return options

        if value_type == BetValueType.TEAM:
            seen = set()
            options = []
            for entry in roster:
                if entry.team.code in seen:
                    continue
                seen.add(entry.team.code)
                options.append(
                    BetQuestionOptionResult(
                        value=entry.team.code,
                        label=entry.team.name,
                        meta={"code": entry.team.code},
                    )
                )
            return options

        if value_type == BetValueType.ENGINE:
            seen = set()
            options = []
            for entry in roster:
                if entry.engine.code in seen:
                    continue
                seen.add(entry.engine.code)
                options.append(
                    BetQuestionOptionResult(
                        value=entry.engine.code,
                        label=entry.engine.name,
                        meta={"code": entry.engine.code},
                    )
                )
            return options

        if value_type == BetValueType.BOOLEAN:
            return [
                BetQuestionOptionResult(value="true", label="Yes"),
                BetQuestionOptionResult(value="false", label="No"),
            ]

        return None

    def _build_race_constraints(
        self,
        *,
        race_event: RaceEvent,
        event_session: EventSession | None,
        value_type: BetValueType,
        constraints_json: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if value_type != BetValueType.POSITION:
            return constraints_json

        roster = self._resolve_race_roster(
            race_event=race_event,
            event_session=event_session,
        )
        resolved_constraints = dict(constraints_json or {})
        resolved_constraints["min"] = 1
        resolved_constraints["max"] = len(roster)
        resolved_constraints["allow_dnf"] = bool(resolved_constraints.get("allow_dnf", False))
        return resolved_constraints

    def _resolve_race_roster(
        self,
        *,
        race_event: RaceEvent,
        event_session: EventSession | None,
    ) -> list[DriverEntry]:
        reference_datetime = self._resolve_race_reference_datetime(
            race_event=race_event,
            event_session=event_session,
        )

        roster_by_seat: dict[tuple[int, int], DriverEntry] = {}

        for entry in race_event.season.driver_entries:
            if entry.race_event_id is not None or entry.event_session_id is not None:
                continue
            if not self._entry_is_active(entry, reference_datetime):
                continue
            roster_by_seat[(entry.team_id, entry.seat_index)] = entry

        for entry in race_event.driver_entries:
            roster_by_seat[(entry.team_id, entry.seat_index)] = entry

        if event_session is not None:
            for entry in event_session.driver_entries:
                roster_by_seat[(entry.team_id, entry.seat_index)] = entry

        return sorted(
            roster_by_seat.values(),
            key=lambda entry: (entry.team.code, entry.seat_index, entry.driver.code),
        )

    def _resolve_race_reference_datetime(
        self,
        *,
        race_event: RaceEvent,
        event_session: EventSession | None,
    ) -> datetime | None:
        if event_session is not None:
            return event_session.start_datetime
        return race_event.event_start or race_event.scheduled_event_start

    def _entry_is_active(self, entry: DriverEntry, reference_datetime: datetime | None) -> bool:
        if reference_datetime is None:
            return True
        if entry.active_from is not None and reference_datetime < entry.active_from:
            return False
        if entry.active_to is not None and reference_datetime >= entry.active_to:
            return False
        return True
    

class GetTestingEventBetQuestions:
    def __init__(self, repository: BetQuestionsRepository):
        self._repository = repository

    def execute(self, *, testing_event_public_id: UUID, group_id: int) -> TestingEventBetQuestionsResult:
        testing_event = self._repository.get_testing_event_by_public_id(testing_event_public_id)
        if testing_event is None:
            raise TestingEventNotFoundForBetQuestionsError()

        bet_context = self._repository.get_pretesting_bet_context(
            group_id=group_id,
            testing_event_id=testing_event.id,
        )
        if bet_context is None:
            raise BetContextNotFoundForTestingEventError()

        templates = self._repository.list_pretesting_templates_for_season(season_id=testing_event.season_id)

        event_template = None
        session_template = None
        for template in templates:
            if template.scope.value == "EVENT":
                event_template = template
            else:
                session_template = template

        event_exceptions = {
            exception.bet_score_id: exception
            for exception in bet_context.bet_exceptions
            if exception.event_session_id is None
        }

        event_questions = []
        if event_template is not None:
            event_questions = self._build_testing_questions(
                testing_event=testing_event,
                testing_event_session=None,
                items=event_template.items,
                fallback_exceptions=event_exceptions,
                specific_exceptions=None,
            )

        sessions: list[TestingEventBetQuestionsSessionResult] = []
        if session_template is not None:
            session_questions = self._build_testing_questions(
                testing_event=testing_event,
                testing_event_session=None,
                items=session_template.items,
                fallback_exceptions=event_exceptions,
                specific_exceptions=None,
            )

            for session in sorted(testing_event.sessions, key=lambda s: s.session_order):
                sessions.append(
                    TestingEventBetQuestionsSessionResult(
                        testing_event_session_public_id=session.public_id,
                        session_order=session.session_order,
                        name=session.name,
                        start_datetime=session.start_datetime,
                        end_datetime=session.end_datetime,
                        scheduled_start_datetime=session.scheduled_start_datetime,
                        scheduled_end_datetime=session.scheduled_end_datetime,
                        questions=session_questions,
                    )
                )

        return TestingEventBetQuestionsResult(
            bet_context_public_id=bet_context.public_id,
            kind=bet_context.kind,
            testing_event_public_id=testing_event.public_id,
            label=bet_context.label,
            status=testing_event.status,
            event_questions=event_questions,
            sessions=sessions,
        )

    def _build_testing_questions(
        self,
        *,
        testing_event: TestingEvent,
        testing_event_session: TestingEventSession | None,
        items: list[BetTemplateItem],
        fallback_exceptions: dict[int, BetException],
        specific_exceptions: dict[int, BetException] | None,
    ) -> list[BetQuestionResult]:
        questions: list[BetQuestionResult] = []

        for item in sorted(items, key=lambda i: (i.display_order, i.id)):
            bet_score = item.bet_score

            exception = None
            if specific_exceptions is not None:
                exception = specific_exceptions.get(bet_score.id)
            if exception is None:
                exception = fallback_exceptions.get(bet_score.id)

            if exception is not None and exception.is_disabled is True:
                continue

            base_points = bet_score.base_points
            constraints_json = bet_score.constraints_json

            if exception is not None and exception.override_points is not None:
                base_points = exception.override_points

            if exception is not None and exception.override_constraints_json is not None:
                constraints_json = exception.override_constraints_json

            constraints_json = self._build_testing_constraints(
                testing_event=testing_event,
                testing_event_session=testing_event_session,
                value_type=bet_score.value_type,
                constraints_json=constraints_json,
            )

            questions.append(
                BetQuestionResult(
                    code=bet_score.code,
                    label=bet_score.label,
                    value_type=bet_score.value_type.value,
                    required=item.required,
                    display_order=item.display_order,
                    base_points=base_points,
                    constraints_json=constraints_json,
                    options=self._build_testing_options(
                        testing_event=testing_event,
                        testing_event_session=testing_event_session,
                        value_type=bet_score.value_type,
                    ),
                )
            )

        return questions

    def _build_testing_options(
        self,
        *,
        testing_event: TestingEvent,
        testing_event_session: TestingEventSession | None,
        value_type: BetValueType,
    ) -> list[BetQuestionOptionResult] | None:
        if value_type in {BetValueType.DRIVER, BetValueType.TEAM, BetValueType.ENGINE, BetValueType.POSITION}:
            roster = self._resolve_testing_roster(
                testing_event=testing_event,
                testing_event_session=testing_event_session,
            )
            driver_numbers_by_driver_id = {
                season_driver.driver_id: season_driver.driver_number
                for season_driver in testing_event.season.season_drivers
            }

        if value_type == BetValueType.DRIVER:
            seen: set[str] = set()
            options: list[BetQuestionOptionResult] = []
            for entry in roster:
                if entry.driver.code in seen:
                    continue
                seen.add(entry.driver.code)
                options.append(
                    BetQuestionOptionResult(
                        value=entry.driver.code,
                        label=entry.driver.name,
                        meta={
                            "code": entry.driver.code,
                            "driver_number": driver_numbers_by_driver_id.get(entry.driver_id),
                        },
                    )
                )
            return options

        if value_type == BetValueType.TEAM:
            seen = set()
            options = []
            for entry in roster:
                if entry.team.code in seen:
                    continue
                seen.add(entry.team.code)
                options.append(
                    BetQuestionOptionResult(
                        value=entry.team.code,
                        label=entry.team.name,
                        meta={"code": entry.team.code},
                    )
                )
            return options

        if value_type == BetValueType.ENGINE:
            seen = set()
            options = []
            for entry in roster:
                if entry.engine.code in seen:
                    continue
                seen.add(entry.engine.code)
                options.append(
                    BetQuestionOptionResult(
                        value=entry.engine.code,
                        label=entry.engine.name,
                        meta={"code": entry.engine.code},
                    )
                )
            return options

        if value_type == BetValueType.BOOLEAN:
            return [
                BetQuestionOptionResult(value="true", label="Yes"),
                BetQuestionOptionResult(value="false", label="No"),
            ]

        return None

    def _build_testing_constraints(
        self,
        *,
        testing_event: TestingEvent,
        testing_event_session: TestingEventSession | None,
        value_type: BetValueType,
        constraints_json: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if value_type != BetValueType.POSITION:
            return constraints_json

        roster = self._resolve_testing_roster(
            testing_event=testing_event,
            testing_event_session=testing_event_session,
        )
        resolved_constraints = dict(constraints_json or {})
        resolved_constraints["min"] = 1
        resolved_constraints["max"] = len(roster)
        resolved_constraints["allow_dnf"] = bool(resolved_constraints.get("allow_dnf", False))
        return resolved_constraints

    def _resolve_testing_roster(
        self,
        *,
        testing_event: TestingEvent,
        testing_event_session: TestingEventSession | None,
    ) -> list[DriverEntry]:
        reference_datetime = self._resolve_testing_reference_datetime(
            testing_event=testing_event,
            testing_event_session=testing_event_session,
        )

        roster_by_seat: dict[tuple[int, int], DriverEntry] = {}
        for entry in testing_event.season.driver_entries:
            if entry.race_event_id is not None or entry.event_session_id is not None:
                continue
            if not self._entry_is_active(entry, reference_datetime):
                continue
            roster_by_seat[(entry.team_id, entry.seat_index)] = entry

        return sorted(
            roster_by_seat.values(),
            key=lambda entry: (entry.team.code, entry.seat_index, entry.driver.code),
        )

    def _resolve_testing_reference_datetime(
        self,
        *,
        testing_event: TestingEvent,
        testing_event_session: TestingEventSession | None,
    ) -> datetime | None:
        if testing_event_session is not None:
            return (
                testing_event_session.start_datetime
                or testing_event_session.scheduled_start_datetime
            )
        return testing_event.event_start or testing_event.scheduled_event_start
