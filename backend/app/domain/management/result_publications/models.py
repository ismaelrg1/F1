from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ResultPublicationResult:
    race_event_public_id: UUID | None
    event_session_public_id: UUID | None
    testing_event_public_id: UUID | None
    testing_event_session_public_id: UUID | None
    season_year: int | None
    published_at: datetime | None
    note: str | None
    published: bool = True
    reason: str | None = None
