from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.db.scoring.official_result import SourceType
from app.domain.management.official_results.answers.models import OfficialResultInput


@dataclass(frozen=True)
class OfficialResult:
    id: int
    bet_context_public_id: UUID
    event_session_public_id: UUID | None
    testing_event_session_public_id: UUID | None
    bet_score_code: str
    label: str
    value: str
    source: SourceType
    created_at: datetime
