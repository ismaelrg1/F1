from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyRankingRepository
from app.api.deps import require_group_member, _translate_ranking_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group
from app.domain.ranking import GetRanking, RankingError
from app.models.ranking import (
    RankingPointsRead,
    RankingResponse,
    RankingTeamRead,
    RankingTeamRowRead,
    RankingTeamTimelineRead,
    RankingTimelinePointRead,
    RankingTimelineRead,
    RankingUserRead,
    RankingUserRowRead,
    RankingUserTimelineRead,
)

router = APIRouter()


@router.get(
    "",
    response_model=RankingResponse,
    response_model_exclude_none=True,
)
def get_ranking(
    request: Request,
    season_year: int = Query(..., ge=1950, le=2100),
    db: Session = Depends(get_db),
    user_group: tuple[User, Group] = Depends(require_group_member),
) -> RankingResponse:
    _, group = user_group
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyRankingRepository(db)
    use_case = GetRanking(repository)

    try:
        result = use_case.execute(
            group_id=group.id,
            season_year=season_year,
        )
    except RankingError as exc:
        raise _translate_ranking_error(exc, locale=locale) from exc

    return RankingResponse(
        season_year=result.season_year,
        ranking_mode=result.ranking_mode,
        updated_at=result.updated_at,
        users=[_map_user_row(row) for row in result.users],
        teams=[_map_team_row(row) for row in result.teams],
        timeline=RankingTimelineRead(
            users=[
                RankingUserTimelineRead(
                    user=_map_user(item.user),
                    points=[_map_timeline_point(point) for point in item.points],
                )
                for item in result.timeline.users
            ],
            teams=[
                RankingTeamTimelineRead(
                    team=_map_team(item.team),
                    points=[_map_timeline_point(point) for point in item.points],
                )
                for item in result.timeline.teams
            ],
        ),
    )


def _map_points(points) -> RankingPointsRead:
    return RankingPointsRead(
        race=points.race,
        testing=points.testing,
        season=points.season,
        powerup=points.powerup,
        total=points.total,
    )


def _map_user(user) -> RankingUserRead:
    return RankingUserRead(
        public_id=user.public_id,
        username=user.username,
        display_name=user.display_name,
        team_public_id=user.team_public_id,
        team_name=user.team_name,
    )


def _map_team(team) -> RankingTeamRead:
    return RankingTeamRead(
        public_id=team.public_id,
        name=team.name,
    )


def _map_user_row(row) -> RankingUserRowRead:
    return RankingUserRowRead(
        position=row.position,
        previous_position=row.previous_position,
        user=_map_user(row.user),
        points=_map_points(row.points),
        last_event_type=row.last_event_type,
        last_event_label=row.last_event_label,
        last_scored_at=row.last_scored_at,
    )


def _map_team_row(row) -> RankingTeamRowRead:
    return RankingTeamRowRead(
        position=row.position,
        previous_position=row.previous_position,
        team=_map_team(row.team),
        points=_map_points(row.points),
        last_event_type=row.last_event_type,
        last_event_label=row.last_event_label,
        last_scored_at=row.last_scored_at,
    )


def _map_timeline_point(point) -> RankingTimelinePointRead:
    return RankingTimelinePointRead(
        event_order=point.event_order,
        event_type=point.event_type,
        label=point.label,
        published_at=point.published_at,
        points=point.points,
    )
