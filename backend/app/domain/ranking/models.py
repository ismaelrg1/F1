from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.db.enums import RankingEventType


@dataclass(frozen=True)
class RankingPoints:
    race: float = 0
    testing: float = 0
    season: float = 0
    powerup: float = 0
    total: float = 0


@dataclass(frozen=True)
class RankingUser:
    public_id: UUID
    username: str
    display_name: str | None
    team_public_id: UUID | None = None
    team_name: str | None = None


@dataclass(frozen=True)
class RankingTeam:
    public_id: UUID
    name: str


@dataclass(frozen=True)
class RankingUserRow:
    position: int
    previous_position: int | None
    user: RankingUser
    points: RankingPoints
    last_event_type: RankingEventType | None = None
    last_event_label: str | None = None
    last_scored_at: datetime | None = None


@dataclass(frozen=True)
class RankingTeamRow:
    position: int
    previous_position: int | None
    team: RankingTeam
    points: RankingPoints
    last_event_type: RankingEventType | None = None
    last_event_label: str | None = None
    last_scored_at: datetime | None = None


@dataclass(frozen=True)
class RankingTimelinePoint:
    event_order: int
    event_type: RankingEventType
    label: str
    published_at: datetime
    points: float


@dataclass(frozen=True)
class RankingUserTimeline:
    user: RankingUser
    points: list[RankingTimelinePoint] = field(default_factory=list)


@dataclass(frozen=True)
class RankingTeamTimeline:
    team: RankingTeam
    points: list[RankingTimelinePoint] = field(default_factory=list)


@dataclass(frozen=True)
class RankingTimeline:
    users: list[RankingUserTimeline]
    teams: list[RankingTeamTimeline]


@dataclass(frozen=True)
class RankingResult:
    season_year: int
    ranking_mode: str
    updated_at: datetime | None
    users: list[RankingUserRow]
    teams: list[RankingTeamRow]
    timeline: RankingTimeline
