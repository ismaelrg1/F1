from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.auth import User
from app.db.betting import BetContext
from app.db.competition import EventSession, RaceEvent, Season, TestingEvent, TestingEventSession
from app.db.enums import BetContextKind, RankingEventType, ScoreComponentType
from app.db.scoring import ResultPublication, Score, ScoreComponent, ScoreSeasonAggregate, ScoreSession, ScoreSessionComponent
from app.db.social import Group, GroupSeasonMembership, Team, TeamSeasonMembership
from app.domain.ranking.models import (
    RankingPoints,
    RankingResult,
    RankingTeam,
    RankingTeamRow,
    RankingTeamTimeline,
    RankingTimeline,
    RankingTimelinePoint,
    RankingUser,
    RankingUserRow,
    RankingUserTimeline,
)

from app.domain.ranking.ports import RankingRepository


@dataclass(frozen=True)
class _PublishedRankingEvent:
    publication_id: int
    bet_context_id: int
    event_type: RankingEventType
    label: str
    event_order: int
    published_at: datetime
    race_event_id: int | None = None
    event_session_id: int | None = None
    testing_event_id: int | None = None
    testing_event_session_id: int | None = None

@dataclass(frozen=True)
class _VisibleRankingMeta:
    last_event_type: RankingEventType | None = None
    last_event_label: str | None = None
    last_scored_at: datetime | None = None


class SqlAlchemyRankingRepository(RankingRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_ranking(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> RankingResult | None:
        season = self._session.execute(
            select(Season).where(Season.year == season_year)
        ).scalar_one_or_none()

        if season is None:
            return None

        group = self._session.execute(
            select(Group).where(Group.id == group_id)
        ).scalar_one()

        ranking_mode = "TEAM" if group.teams_enabled else "USER"

        users_by_id = (
            self._list_team_group_users(group_id=group_id, season_id=season.id)
            if group.teams_enabled
            else self._list_group_users(group_id=group_id, season_id=season.id)
        )
        teams_by_id = self._list_group_teams(group_id=group_id, season_id=season.id) if group.teams_enabled else {}
        team_by_user_id = self._team_by_user_id(group_id=group_id, season_id=season.id) if group.teams_enabled else {}

        published_events = self._published_events(
            group_id=group_id,
            season_id=season.id,
        )

        (
            event_points_by_publication_id,
            visible_points_by_user_id,
            visible_meta_by_user_id,
        ) = self._visible_points_from_published_events(events=published_events)

        if published_events:
            (
                _previous_event_points_by_publication_id,
                previous_visible_points_by_user_id,
                _previous_visible_meta_by_user_id,
            ) = self._visible_points_from_published_events(events=published_events[:-1])
        else:
            previous_visible_points_by_user_id = {}

        previous_user_positions = self._rank_positions_by_user(
            users_by_id=users_by_id,
            visible_points_by_user_id=previous_visible_points_by_user_id,
        )

        previous_team_positions = (
            self._rank_positions_by_team(
                teams_by_id=teams_by_id,
                team_by_user_id=team_by_user_id,
                visible_points_by_user_id=previous_visible_points_by_user_id,
            )
            if group.teams_enabled
            else {}
        )

        user_rows = self._build_user_rows(
            users_by_id=users_by_id,
            visible_points_by_user_id=visible_points_by_user_id,
            visible_meta_by_user_id=visible_meta_by_user_id,
            previous_user_positions=previous_user_positions,
        )

        team_rows = (
            self._build_team_rows(
                teams_by_id=teams_by_id,
                team_by_user_id=team_by_user_id,
                visible_points_by_user_id=visible_points_by_user_id,
                visible_meta_by_user_id=visible_meta_by_user_id,
                previous_team_positions=previous_team_positions,
            )
            if group.teams_enabled
            else []
        )

        timeline = self._build_timeline(
            ranking_mode=ranking_mode,
            events=published_events,
            users_by_id=users_by_id,
            teams_by_id=teams_by_id,
            team_by_user_id=team_by_user_id,
            event_points_by_publication_id=event_points_by_publication_id,
        )

        updated_at = max(
            (
                meta.last_scored_at
                for meta in visible_meta_by_user_id.values()
                if meta.last_scored_at is not None
            ),
            default=None,
        )

        return RankingResult(
            season_year=season.year,
            ranking_mode=ranking_mode,
            updated_at=updated_at,
            users=user_rows,
            teams=team_rows,
            timeline=timeline,
        )

    def _list_group_users(self, *, group_id: int, season_id: int) -> dict[int, RankingUser]:
        stmt = (
            select(User)
            .join(GroupSeasonMembership, GroupSeasonMembership.user_id == User.id)
            .where(
                GroupSeasonMembership.group_id == group_id,
                GroupSeasonMembership.season_id == season_id,
                GroupSeasonMembership.is_active.is_(True),
            )
            .order_by(User.username)
        )

        users = self._session.execute(stmt).scalars().all()

        return {
            user.id: RankingUser(
                public_id=user.public_id,
                username=user.username,
                display_name=getattr(user, "display_name", None),
            )
            for user in users
        }

    def _list_team_group_users(self, *, group_id: int, season_id: int) -> dict[int, RankingUser]:
        stmt = (
            select(User, Team)
            .join(TeamSeasonMembership, TeamSeasonMembership.user_id == User.id)
            .join(Team, Team.id == TeamSeasonMembership.team_id)
            .where(
                TeamSeasonMembership.group_id == group_id,
                TeamSeasonMembership.season_id == season_id,
                TeamSeasonMembership.is_active.is_(True),
            )
            .order_by(User.username)
        )

        rows = self._session.execute(stmt).all()

        return {
            user.id: RankingUser(
                public_id=user.public_id,
                username=user.username,
                display_name=getattr(user, "display_name", None),
                team_public_id=team.public_id,
                team_name=team.name,
            )
            for user, team in rows
        }

    def _list_group_teams(self, *, group_id: int, season_id: int) -> dict[int, RankingTeam]:
        stmt = (
            select(Team)
            .join(TeamSeasonMembership, TeamSeasonMembership.team_id == Team.id)
            .where(
                TeamSeasonMembership.group_id == group_id,
                TeamSeasonMembership.season_id == season_id,
                TeamSeasonMembership.is_active.is_(True),
            )
            .distinct()
            .order_by(Team.name)
        )

        teams = self._session.execute(stmt).scalars().all()

        return {
            team.id: RankingTeam(
                public_id=team.public_id,
                name=team.name,
            )
            for team in teams
        }

    def _team_by_user_id(self, *, group_id: int, season_id: int) -> dict[int, int]:
        stmt = (
            select(TeamSeasonMembership.user_id, TeamSeasonMembership.team_id)
            .where(
                TeamSeasonMembership.group_id == group_id,
                TeamSeasonMembership.season_id == season_id,
                TeamSeasonMembership.is_active.is_(True),
            )
        )

        return {
            user_id: team_id
            for user_id, team_id in self._session.execute(stmt).all()
        }

    def _season_aggregates_by_user_id(
        self,
        *,
        group_id: int,
        season_id: int,
    ) -> dict[int, ScoreSeasonAggregate]:
        stmt = (
            select(ScoreSeasonAggregate)
            .where(
                ScoreSeasonAggregate.group_id == group_id,
                ScoreSeasonAggregate.season_id == season_id,
            )
        )

        aggregates = self._session.execute(stmt).scalars().all()
        return {aggregate.user_id: aggregate for aggregate in aggregates}

    def _published_events(
        self,
        *,
        group_id: int,
        season_id: int,
    ) -> list[_PublishedRankingEvent]:
        stmt = (
            select(BetContext, ResultPublication, RaceEvent, TestingEvent)
            .join(ResultPublication, ResultPublication.bet_context_id == BetContext.id)
            .outerjoin(RaceEvent, RaceEvent.id == BetContext.race_event_id)
            .outerjoin(TestingEvent, TestingEvent.id == BetContext.testing_event_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.season_id == season_id,
            )
        )

        events: list[_PublishedRankingEvent] = []

        for bet_context, publication, race_event, testing_event in self._session.execute(stmt).all():
            if bet_context.kind == BetContextKind.PRETESTING and testing_event is not None:
                events.append(
                    _PublishedRankingEvent(
                        publication_id=publication.id,
                        bet_context_id=bet_context.id,
                        event_type=RankingEventType.TESTING_EVENT,
                        label=bet_context.label,
                        event_order=0,
                        published_at=publication.published_at,
                        testing_event_id=testing_event.id,
                        testing_event_session_id=publication.testing_event_session_id,
                    )
                )

            elif bet_context.kind == BetContextKind.GP and race_event is not None:
                events.append(
                    _PublishedRankingEvent(
                        publication_id=publication.id,
                        bet_context_id=bet_context.id,
                        event_type=RankingEventType.RACE_EVENT,
                        label=bet_context.label,
                        event_order=race_event.round_number,
                        published_at=publication.published_at,
                        race_event_id=race_event.id,
                        event_session_id=publication.event_session_id,
                    )
                )

            elif bet_context.kind == BetContextKind.SEASON:
                events.append(
                    _PublishedRankingEvent(
                        publication_id=publication.id,
                        bet_context_id=bet_context.id,
                        event_type=RankingEventType.SEASON,
                        label=bet_context.label,
                        event_order=10_000,
                        published_at=publication.published_at,
                    )
                )

        return sorted(events, key=lambda item: (item.event_order, item.published_at, item.label))

    def _visible_points_from_published_events(
        self,
        *,
        events: list[_PublishedRankingEvent],
    ) -> tuple[
        dict[int, dict[int, RankingPoints]],
        dict[int, RankingPoints],
        dict[int, _VisibleRankingMeta],
    ]:
        event_points_by_publication_id: dict[int, dict[int, RankingPoints]] = {}
        visible_points_by_user_id: dict[int, RankingPoints] = defaultdict(RankingPoints)
        visible_meta_by_user_id: dict[int, _VisibleRankingMeta] = {}

        for event in events:
            event_points = self._event_points_breakdown_by_user_id(event)
            event_points_by_publication_id[event.publication_id] = event_points

            for user_id, event_points_value in event_points.items():
                current = visible_points_by_user_id[user_id]

                visible_points_by_user_id[user_id] = RankingPoints(
                    race=current.race + event_points_value.race,
                    testing=current.testing + event_points_value.testing,
                    season=current.season + event_points_value.season,
                    extra=current.extra + event_points_value.extra,
                    penalty=current.penalty + event_points_value.penalty,
                    total=current.total + event_points_value.total,
                )

                visible_meta_by_user_id[user_id] = _VisibleRankingMeta(
                    last_event_type=event.event_type,
                    last_event_label=event.label,
                    last_scored_at=event.published_at,
                )

        return (
            event_points_by_publication_id,
            dict(visible_points_by_user_id),
            visible_meta_by_user_id,
        )

    def _event_points_breakdown_by_user_id(
        self,
        event: _PublishedRankingEvent,
    ) -> dict[int, RankingPoints]:
        points_by_user_id: dict[int, RankingPoints] = defaultdict(RankingPoints)

        for score in self._event_level_scores(event):
            current = points_by_user_id[score.user_id]
            bucket_points, extra_points, penalty_points = self._score_component_breakdown(
                components=score.score_components,
                fallback_base=self._to_float(score.base_points),
                fallback_total=self._to_float(score.total_points),
                event_type=event.event_type,
            )

            points_by_user_id[score.user_id] = RankingPoints(
                race=current.race + bucket_points.race,
                testing=current.testing + bucket_points.testing,
                season=current.season + bucket_points.season,
                extra=current.extra + extra_points,
                penalty=current.penalty + penalty_points,
                total=current.total + bucket_points.total + extra_points - penalty_points,
            )

        for score_session in self._session_level_scores(event):
            current = points_by_user_id[score_session.user_id]
            bucket_points, extra_points, penalty_points = self._score_component_breakdown(
                components=score_session.score_session_components,
                fallback_base=self._to_float(score_session.base_points),
                fallback_total=self._to_float(score_session.total_points),
                event_type=event.event_type,
            )

            points_by_user_id[score_session.user_id] = RankingPoints(
                race=current.race + bucket_points.race,
                testing=current.testing + bucket_points.testing,
                season=current.season + bucket_points.season,
                extra=current.extra + extra_points,
                penalty=current.penalty + penalty_points,
                total=current.total + bucket_points.total + extra_points - penalty_points,
            )

        return dict(points_by_user_id)

    def _event_level_scores(
        self,
        event: _PublishedRankingEvent,
    ) -> list[Score]:
        stmt = (
            select(Score)
            .where(Score.bet_context_id == event.bet_context_id)
            .options(selectinload(Score.score_components))
        )

        if event.event_session_id is not None or event.testing_event_session_id is not None:
            return []

        return list(self._session.execute(stmt).scalars().unique().all())

    def _session_level_scores(
        self,
        event: _PublishedRankingEvent,
    ) -> list[ScoreSession]:
        stmt = (
            select(ScoreSession)
            .where(ScoreSession.bet_context_id == event.bet_context_id)
            .options(selectinload(ScoreSession.score_session_components))
        )

        if event.event_type == RankingEventType.RACE_EVENT:
            if event.event_session_id is not None:
                stmt = stmt.where(ScoreSession.event_session_id == event.event_session_id)
            else:
                session_ids_stmt = select(EventSession.id).where(
                    EventSession.race_event_id == event.race_event_id
                )
                stmt = stmt.where(ScoreSession.event_session_id.in_(session_ids_stmt))

        elif event.event_type == RankingEventType.TESTING_EVENT:
            if event.testing_event_session_id is not None:
                stmt = stmt.where(
                    ScoreSession.testing_event_session_id == event.testing_event_session_id
                )
            else:
                session_ids_stmt = select(TestingEventSession.id).where(
                    TestingEventSession.testing_event_id == event.testing_event_id
                )
                stmt = stmt.where(ScoreSession.testing_event_session_id.in_(session_ids_stmt))

        else:
            return []

        return list(self._session.execute(stmt).scalars().unique().all())

    def _score_component_breakdown(
        self,
        *,
        components: list[ScoreComponent] | list[ScoreSessionComponent],
        fallback_base: float,
        fallback_total: float,
        event_type: RankingEventType,
    ) -> tuple[RankingPoints, float, float]:
        base_points = 0.0
        powerup_points = 0.0
        extra_points = 0.0
        penalty_points = 0.0

        for component in components:
            points = self._to_float(component.points)

            if component.component_type == ScoreComponentType.BASE:
                base_points += points
            elif component.component_type == ScoreComponentType.POWERUP:
                powerup_points += points
            elif component.component_type == ScoreComponentType.EXTRA:
                extra_points += points
            elif component.component_type == ScoreComponentType.PENALTY:
                penalty_points += points

        if not components:
            base_points = fallback_base
            extra_points = max(fallback_total - fallback_base, 0.0)

        bucket_total = base_points + powerup_points

        if event_type == RankingEventType.RACE_EVENT:
            bucket_points = RankingPoints(race=bucket_total, total=bucket_total)
        elif event_type == RankingEventType.TESTING_EVENT:
            bucket_points = RankingPoints(testing=bucket_total, total=bucket_total)
        else:
            bucket_points = RankingPoints(season=bucket_total, total=bucket_total)

        return bucket_points, extra_points, penalty_points

    def _build_user_rows(
        self,
        *,
        users_by_id: dict[int, RankingUser],
        visible_points_by_user_id: dict[int, RankingPoints],
        visible_meta_by_user_id: dict[int, _VisibleRankingMeta],
        previous_user_positions: dict[int, int | None],
    ) -> list[RankingUserRow]:
        rows: list[RankingUserRow] = []

        for user_id, user in users_by_id.items():
            meta = visible_meta_by_user_id.get(user_id, _VisibleRankingMeta())

            rows.append(
                RankingUserRow(
                    position=0,
                    previous_position=previous_user_positions.get(user_id),
                    user=user,
                    points=visible_points_by_user_id.get(user_id, RankingPoints()),
                    last_event_type=meta.last_event_type,
                    last_event_label=meta.last_event_label,
                    last_scored_at=meta.last_scored_at,
                )
            )

        return self._rank_user_rows(rows)

    def _build_team_rows(
        self,
        *,
        teams_by_id: dict[int, RankingTeam],
        team_by_user_id: dict[int, int],
        visible_points_by_user_id: dict[int, RankingPoints],
        visible_meta_by_user_id: dict[int, _VisibleRankingMeta],
        previous_team_positions: dict[int, int | None],
    ) -> list[RankingTeamRow]:
        points_by_team_id: dict[int, RankingPoints] = {
            team_id: RankingPoints()
            for team_id in teams_by_id
        }
        last_scored_at_by_team_id: dict[int, datetime | None] = {
            team_id: None
            for team_id in teams_by_id
        }

        for user_id, team_id in team_by_user_id.items():
            current = points_by_team_id.get(team_id, RankingPoints())
            user_points = visible_points_by_user_id.get(user_id, RankingPoints())

            points_by_team_id[team_id] = RankingPoints(
                race=current.race + user_points.race,
                testing=current.testing + user_points.testing,
                season=current.season + user_points.season,
                extra=current.extra + user_points.extra,
                penalty=current.penalty + user_points.penalty,
                total=current.total + user_points.total,
            )

            meta = visible_meta_by_user_id.get(user_id)
            if meta is not None and meta.last_scored_at is not None:
                previous = last_scored_at_by_team_id.get(team_id)
                if previous is None or meta.last_scored_at > previous:
                    last_scored_at_by_team_id[team_id] = meta.last_scored_at

        rows = [
            RankingTeamRow(
                position=0,
                previous_position=previous_team_positions.get(team_id),
                team=team,
                points=points_by_team_id.get(team_id, RankingPoints()),
                last_scored_at=last_scored_at_by_team_id.get(team_id),
            )
            for team_id, team in teams_by_id.items()
        ]

        return self._rank_team_rows(rows)

    def _build_timeline(
        self,
        *,
        ranking_mode: str,
        events: list[_PublishedRankingEvent],
        users_by_id: dict[int, RankingUser],
        teams_by_id: dict[int, RankingTeam],
        team_by_user_id: dict[int, int],
        event_points_by_publication_id: dict[int, dict[int, RankingPoints]],
    ) -> RankingTimeline:
        cumulative_by_user_id = {
            user_id: 0.0
            for user_id in users_by_id
        }

        user_points: dict[int, list[RankingTimelinePoint]] = {
            user_id: []
            for user_id in users_by_id
        }

        cumulative_by_team_id = {
            team_id: 0.0
            for team_id in teams_by_id
        }

        team_points: dict[int, list[RankingTimelinePoint]] = {
            team_id: []
            for team_id in teams_by_id
        }

        for event in events:
            event_points = event_points_by_publication_id.get(event.publication_id, {})

            for user_id in users_by_id:
                cumulative_by_user_id[user_id] += event_points.get(user_id, RankingPoints()).total
                user_points[user_id].append(
                    RankingTimelinePoint(
                        event_order=event.event_order,
                        event_type=event.event_type,
                        label=event.label,
                        published_at=event.published_at,
                        points=cumulative_by_user_id[user_id],
                    )
                )

            if ranking_mode == "TEAM":
                event_points_by_team_id: defaultdict[int, float] = defaultdict(float)

                for user_id, points in event_points.items():
                    team_id = team_by_user_id.get(user_id)
                    if team_id is not None:
                        event_points_by_team_id[team_id] += points.total

                for team_id in teams_by_id:
                    cumulative_by_team_id[team_id] += event_points_by_team_id.get(team_id, 0.0)
                    team_points[team_id].append(
                        RankingTimelinePoint(
                            event_order=event.event_order,
                            event_type=event.event_type,
                            label=event.label,
                            published_at=event.published_at,
                            points=cumulative_by_team_id[team_id],
                        )
                    )

        return RankingTimeline(
            users=[
                RankingUserTimeline(
                    user=user,
                    points=user_points[user_id],
                )
                for user_id, user in users_by_id.items()
            ],
            teams=[
                RankingTeamTimeline(
                    team=team,
                    points=team_points[team_id],
                )
                for team_id, team in teams_by_id.items()
            ],
        )

    def _rank_positions_by_user(
        self,
        *,
        users_by_id: dict[int, RankingUser],
        visible_points_by_user_id: dict[int, RankingPoints],
    ) -> dict[int, int | None]:
        ordered_user_ids = [
            user_id
            for user_id, _user in sorted(
                users_by_id.items(),
                key=lambda item: (
                    -visible_points_by_user_id.get(item[0], RankingPoints()).total,
                    item[1].username.lower(),
                ),
            )
        ]

        if not ordered_user_ids:
            return {}

        return {
            user_id: index
            for index, user_id in enumerate(ordered_user_ids, start=1)
        }

    def _rank_positions_by_team(
        self,
        *,
        teams_by_id: dict[int, RankingTeam],
        team_by_user_id: dict[int, int],
        visible_points_by_user_id: dict[int, RankingPoints],
    ) -> dict[int, int | None]:
        points_by_team_id: dict[int, float] = {
            team_id: 0.0
            for team_id in teams_by_id
        }

        for user_id, team_id in team_by_user_id.items():
            points_by_team_id[team_id] += visible_points_by_user_id.get(user_id, RankingPoints()).total

        ordered_team_ids = [
            team_id
            for team_id, _team in sorted(
                teams_by_id.items(),
                key=lambda item: (
                    -points_by_team_id.get(item[0], 0.0),
                    item[1].name.lower(),
                ),
            )
        ]

        if not ordered_team_ids:
            return {}

        return {
            team_id: index
            for index, team_id in enumerate(ordered_team_ids, start=1)
        }

    def _rank_user_rows(self, rows: list[RankingUserRow]) -> list[RankingUserRow]:
        ordered = sorted(
            rows,
            key=lambda row: (-row.points.total, row.user.username.lower()),
        )

        return [
            RankingUserRow(
                position=index,
                previous_position=row.previous_position,
                user=row.user,
                points=row.points,
                last_event_type=row.last_event_type,
                last_event_label=row.last_event_label,
                last_scored_at=row.last_scored_at,
            )
            for index, row in enumerate(ordered, start=1)
        ]

    def _rank_team_rows(self, rows: list[RankingTeamRow]) -> list[RankingTeamRow]:
        ordered = sorted(
            rows,
            key=lambda row: (-row.points.total, row.team.name.lower()),
        )

        return [
            RankingTeamRow(
                position=index,
                previous_position=row.previous_position,
                team=row.team,
                points=row.points,
                last_event_type=row.last_event_type,
                last_event_label=row.last_event_label,
                last_scored_at=row.last_scored_at,
            )
            for index, row in enumerate(ordered, start=1)
        ]

    def _to_float(self, value: Decimal | int | float | None) -> float:
        if value is None:
            return 0.0

        return float(value)
