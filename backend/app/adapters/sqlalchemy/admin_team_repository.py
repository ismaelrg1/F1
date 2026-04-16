from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.competition import Season, SeasonTeam, TeamF1
from app.domain.admin.teams.models import (
    AdminSeasonTeam,
    AdminTeam,
    AdminTeamSeason,
)
from app.domain.admin.teams.ports import AdminTeamRepository


class SqlAlchemyAdminTeamRepository(AdminTeamRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_code(self, code: str) -> AdminTeam | None:
        stmt = select(TeamF1).where(TeamF1.code == code)
        team = self._session.execute(stmt).scalar_one_or_none()
        if team is None:
            return None
        return AdminTeam(
            id=team.id,
            code=team.code,
            name=team.name,
        )

    def create(self, *, code: str, name: str) -> AdminTeam:
        team = TeamF1(code=code, name=name)
        self._session.add(team)
        self._session.flush()
        self._session.refresh(team)
        return AdminTeam(
            id=team.id,
            code=team.code,
            name=team.name,
        )

    def get_season_by_year(self, year: int) -> AdminTeamSeason | None:
        stmt = select(Season).where(Season.year == year)
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None
        return AdminTeamSeason(
            id=season.id,
            year=season.year,
        )

    def get_season_team(self, *, season_id: int, team_id: int) -> AdminSeasonTeam | None:
        stmt = (
            select(SeasonTeam)
            .where(
                SeasonTeam.season_id == season_id,
                SeasonTeam.team_id == team_id,
            )
            .options(
                joinedload(SeasonTeam.season),
                joinedload(SeasonTeam.team),
            )
        )
        season_team = self._session.execute(stmt).scalar_one_or_none()
        if season_team is None:
            return None
        return self._map_season_team(season_team)

    def create_season_team(
        self,
        *,
        season_id: int,
        team_id: int,
        is_active: bool,
    ) -> AdminSeasonTeam:
        season_team = SeasonTeam(
            season_id=season_id,
            team_id=team_id,
            is_active=is_active,
        )
        self._session.add(season_team)
        self._session.flush()

        stmt = (
            select(SeasonTeam)
            .where(
                SeasonTeam.season_id == season_team.season_id,
                SeasonTeam.team_id == season_team.team_id,
            )
            .options(
                joinedload(SeasonTeam.season),
                joinedload(SeasonTeam.team),
            )
        )
        created = self._session.execute(stmt).scalar_one()
        return self._map_season_team(created)

    def _map_season_team(self, season_team: SeasonTeam) -> AdminSeasonTeam:
        return AdminSeasonTeam(
            season_year=season_team.season.year,
            team_code=season_team.team.code,
            is_active=season_team.is_active,
        )