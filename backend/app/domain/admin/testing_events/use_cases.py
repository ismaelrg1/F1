from app.domain.admin.testing_events.errors import (
    CircuitNotFoundForTestingEventError,
    DuplicateTestingEventSessionOrderError,
    SeasonNotFoundForTestingEventError,
    TestingEventAlreadyExistsError,
)
from app.domain.admin.testing_events.ports import AdminTestingEventRepository


class CreateTestingEvent:
    def __init__(self, repository: AdminTestingEventRepository):
        self._repository = repository

    def execute(
        self,
        *,
        season_year: int,
        circuit_code: str,
        name: str,
        event_start,
        event_end,
        scheduled_event_start,
        scheduled_event_end,
        status_reason: str | None,
        sessions: list[dict],
    ):
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForTestingEventError(season_year)

        normalized_circuit_code = circuit_code.strip().lower()

        circuit = self._repository.get_circuit_by_code(normalized_circuit_code)
        if circuit is None:
            raise CircuitNotFoundForTestingEventError(normalized_circuit_code)

        existing = self._repository.get_by_season_and_name(season_id=season.id, name=name)
        if existing is not None:
            raise TestingEventAlreadyExistsError(season_year=season.year, name=name)

        seen_orders: set[int] = set()
        for session in sessions:
            order = session["session_order"]
            if order in seen_orders:
                raise DuplicateTestingEventSessionOrderError(order)
            seen_orders.add(order)

        return self._repository.create(
            season_id=season.id,
            circuit_id=circuit.id,
            name=name,
            event_start=event_start,
            event_end=event_end,
            scheduled_event_start=scheduled_event_start,
            scheduled_event_end=scheduled_event_end,
            status_reason=status_reason,
            sessions=sessions,
        )
