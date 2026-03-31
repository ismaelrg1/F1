from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Season, SeasonTeam, TeamF1
from app.domain.admin.teams.ports import AdminTeamRepository


class SqlAlchemyAdminTeamRepository(AdminTeamRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_code(self, code: str) -> TeamF1 | None:
        stmt = select(TeamF1).where(TeamF1.code == code)
        return self._session.execute(stmt).scalar_one_or_none()

    def create(self, *, code: str, name: str) -> TeamF1:
        team = TeamF1(code=code, name=name)
        self._session.add(team)
        self._session.flush()
        self._session.refresh(team)
        return team

    def get_season_by_year(self, year: int) -> Season | None:
        stmt = select(Season).where(Season.year == year)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_season_team(self, *, season_id: int, team_id: int) -> SeasonTeam | None:
        stmt = select(SeasonTeam).where(
            SeasonTeam.season_id == season_id,
            SeasonTeam.team_id == team_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def create_season_team(self, *, season_id: int, team_id: int, is_active: bool) -> SeasonTeam:
        season_team = SeasonTeam(
            season_id=season_id,
            team_id=team_id,
            is_active=is_active,
        )
        self._session.add(season_team)
        self._session.flush()
        self._session.refresh(season_team)
        return season_team