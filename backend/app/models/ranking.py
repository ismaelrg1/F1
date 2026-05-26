from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.db.enums import RankingEventType


class RankingPointsRead(BaseModel):
    race: float = 0
    testing: float = 0
    season: float = 0
    extra: float = 0
    penalty: float = 0
    total: float = 0


class RankingUserRead(BaseModel):
    public_id: UUID
    username: str
    display_name: str | None = None
    team_public_id: UUID | None = None
    team_name: str | None = None


class RankingTeamRead(BaseModel):
    public_id: UUID
    name: str


class RankingUserRowRead(BaseModel):
    position: int
    previous_position: int | None = None
    user: RankingUserRead
    points: RankingPointsRead
    last_event_type: RankingEventType | None = None
    last_event_label: str | None = None
    last_scored_at: datetime | None = None


class RankingTeamRowRead(BaseModel):
    position: int
    previous_position: int | None = None
    team: RankingTeamRead
    points: RankingPointsRead
    last_event_type: RankingEventType | None = None
    last_event_label: str | None = None
    last_scored_at: datetime | None = None


class RankingTimelinePointRead(BaseModel):
    event_order: int
    event_type: RankingEventType
    label: str
    published_at: datetime
    points: float


class RankingUserTimelineRead(BaseModel):
    user: RankingUserRead
    points: list[RankingTimelinePointRead]


class RankingTeamTimelineRead(BaseModel):
    team: RankingTeamRead
    points: list[RankingTimelinePointRead]


class RankingTimelineRead(BaseModel):
    users: list[RankingUserTimelineRead]
    teams: list[RankingTeamTimelineRead]


class RankingResponse(BaseModel):
    season_year: int
    ranking_mode: str
    updated_at: datetime | None = None
    users: list[RankingUserRowRead]
    teams: list[RankingTeamRowRead]
    timeline: RankingTimelineRead