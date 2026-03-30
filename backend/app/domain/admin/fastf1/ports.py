from typing import Protocol, Any

class AdminFastF1Repository(Protocol):
    def list_race_event_previews(self, year: int) -> list[dict[str, Any]]:
        ...
