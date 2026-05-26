from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.db.scoring.official_result import SourceType


@dataclass(frozen=True)
class AdminOfficialResult:
    id: int
    bet_context_public_id: UUID
    event_session_public_id: UUID | None
    testing_event_session_public_id: UUID | None
    bet_score_code: str
    label: str
    value: str
    source: SourceType
    created_at: datetime


@dataclass(frozen=True)
class AdminOfficialResultInput:
    bet_score_code: str
    value: str