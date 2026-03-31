from app.domain.admin.race_events.errors import (
    CircuitNotFoundForRaceEventError,
    DuplicateRaceEventSessionTypeError,
    RaceEventAlreadyExistsError,
    RaceEventNotFoundError,
    SeasonNotFoundForRaceEventError,
)
from app.domain.admin.race_events.ports import AdminRaceEventRepository


class CreateRaceEvent:
    def __init__(self, repository: AdminRaceEventRepository):
        self._repository = repository

    def execute(
        self,
        *,
        season_year: int,
        round_number: int,
        circuit_code: str,
        name: str,
        source_provider,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ):
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForRaceEventError(season_year=season_year)

        normalized_circuit_code = circuit_code.strip().lower()
        circuit = self._repository.get_circuit_by_code(normalized_circuit_code)
        if circuit is None:
            raise CircuitNotFoundForRaceEventError(circuit_code=normalized_circuit_code)

        existing = self._repository.get_by_season_and_round(
            season_id=season.id,
            round_number=round_number,
        )
        if existing is not None:
            raise RaceEventAlreadyExistsError(
                season_year=season.year,
                round_number=round_number,
            )

        seen_session_types: set[str] = set()
        for session in sessions:
            session_type = session["session_type"].value if hasattr(session["session_type"], "value") else str(session["session_type"])
            if session_type in seen_session_types:
                raise DuplicateRaceEventSessionTypeError(session_type=session_type)
            seen_session_types.add(session_type)

        return self._repository.create(
            season_id=season.id,
            circuit_id=circuit.id,
            round_number=round_number,
            name=name,
            source_provider=source_provider,
            source_key=source_key,
            event_start=event_start,
            event_end=event_end,
            scheduled_event_start=scheduled_event_start,
            scheduled_event_end=scheduled_event_end,
            status=status,
            status_reason=status_reason,
            sessions=sessions,
        )


class UpdateRaceEvent:
    def __init__(self, repository: AdminRaceEventRepository):
        self._repository = repository

    def execute(
        self,
        *,
        race_event_id: int,
        season_year: int,
        round_number: int,
        circuit_code: str,
        name: str,
        source_provider,
        source_key: str | None,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status,
        status_reason: str | None,
        sessions: list[dict],
    ):
        race_event = self._repository.get_by_id(race_event_id)
        if race_event is None:
            raise RaceEventNotFoundError(race_event_id=race_event_id)

        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForRaceEventError(season_year=season_year)

        normalized_circuit_code = circuit_code.strip().lower()
        circuit = self._repository.get_circuit_by_code(normalized_circuit_code)
        if circuit is None:
            raise CircuitNotFoundForRaceEventError(circuit_code=normalized_circuit_code)

        existing = self._repository.get_by_season_and_round(
            season_id=season.id,
            round_number=round_number,
        )
        if existing is not None and existing.id != race_event.id:
            raise RaceEventAlreadyExistsError(
                season_year=season.year,
                round_number=round_number,
            )

        seen_session_types: set[str] = set()
        for session in sessions:
            session_type = session["session_type"].value if hasattr(session["session_type"], "value") else str(session["session_type"])
            if session_type in seen_session_types:
                raise DuplicateRaceEventSessionTypeError(session_type=session_type)
            seen_session_types.add(session_type)

        return self._repository.update(
            race_event=race_event,
            season_id=season.id,
            circuit_id=circuit.id,
            round_number=round_number,
            name=name,
            source_provider=source_provider,
            source_key=source_key,
            event_start=event_start,
            event_end=event_end,
            scheduled_event_start=scheduled_event_start,
            scheduled_event_end=scheduled_event_end,
            status=status,
            status_reason=status_reason,
            sessions=sessions,
        )
    
class ListRaceEvents:
    def __init__(self, repository: AdminRaceEventRepository):
        self._repository = repository

    def execute(self, *, season_year: int | None = None):
        return self._repository.list_race_events(season_year=season_year)
