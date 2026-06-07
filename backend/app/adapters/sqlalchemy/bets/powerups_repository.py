from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.adapters.sqlalchemy.bets.base_repository import SqlAlchemyBetBaseRepository
from app.db.betting import BetContext
from app.db.auth import User
from app.db.competition import EventSession, TestingEventSession
from app.db.enums import BetContextKind
from app.db.powerups import PowerUpAssignment, PowerUpRestriction, PowerUpUse, PowerUpUseTarget
from app.db.social import GroupMembership, Team, TeamMembership
from app.domain.bets.powerups.models import BetPowerUpAvailability, BetPowerUpTargetTeamDefinition, BetPowerUpTargetUserDefinition
from app.domain.bets.powerups.ports import BetPowerUpsRepository


class SqlAlchemyBetPowerUpsRepository(SqlAlchemyBetBaseRepository, BetPowerUpsRepository):
    def get_race_bet_context_id(
        self,
        *,
        group_id: int,
        race_event_id: int,
    ) -> int | None:
        return self._session.scalar(
            select(BetContext.id).where(
                BetContext.group_id == group_id,
                BetContext.race_event_id == race_event_id,
                BetContext.kind == BetContextKind.GP,
            )
        )

    def get_testing_bet_context_id(
        self,
        *,
        group_id: int,
        testing_event_id: int,
    ) -> int | None:
        return self._session.scalar(
            select(BetContext.id).where(
                BetContext.group_id == group_id,
                BetContext.testing_event_id == testing_event_id,
                BetContext.kind == BetContextKind.PRETESTING,
            )
        )

    def get_season_bet_context_id(
        self,
        *,
        group_id: int,
        season_id: int,
    ) -> int | None:
        return self._session.scalar(
            select(BetContext.id).where(
                BetContext.group_id == group_id,
                BetContext.season_id == season_id,
                BetContext.kind == BetContextKind.SEASON,
            )
        )

    def get_event_session_id(
        self,
        *,
        race_event_id: int,
        event_session_public_id: UUID,
    ) -> int | None:
        return self._session.scalar(
            select(EventSession.id).where(
                EventSession.race_event_id == race_event_id,
                EventSession.public_id == event_session_public_id,
            )
        )

    def get_testing_event_session_id(
        self,
        *,
        testing_event_id: int,
        testing_event_session_public_id: UUID,
    ) -> int | None:
        return self._session.scalar(
            select(TestingEventSession.id).where(
                TestingEventSession.testing_event_id == testing_event_id,
                TestingEventSession.public_id == testing_event_session_public_id,
            )
        )

    def list_available_powerups(
        self,
        *,
        group_id: int,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> list[BetPowerUpAvailability]:
        assignments = self._session.scalars(
            select(PowerUpAssignment)
            .where(
                PowerUpAssignment.group_id == group_id,
                PowerUpAssignment.user_id == user_id,
                PowerUpAssignment.bet_context_id == bet_context_id,
                PowerUpAssignment.is_active.is_(True),
            )
            .options(joinedload(PowerUpAssignment.powerup))
        ).all()

        return [
            BetPowerUpAvailability(
                powerup_id=assignment.powerup_id,
                code=assignment.powerup.code,
                name=assignment.powerup.name,
                target_mode=assignment.powerup.target_mode,
                quantity=assignment.quantity,
                is_enabled=assignment.powerup.is_enabled,
                is_restricted=self._is_powerup_restricted(
                    powerup_id=assignment.powerup_id,
                    bet_context_id=bet_context_id,
                    event_session_id=event_session_id,
                    testing_event_session_id=testing_event_session_id,
                ),
                already_used=self._powerup_already_used(
                    group_id=group_id,
                    user_id=user_id,
                    bet_context_id=bet_context_id,
                    powerup_id=assignment.powerup_id,
                    event_session_id=event_session_id,
                    testing_event_session_id=testing_event_session_id,
                ),
                target_options=[],
            )
            for assignment in assignments
        ]

    def _is_powerup_restricted(
        self,
        *,
        powerup_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        return self._session.execute(
            select(PowerUpRestriction.id).where(
                PowerUpRestriction.powerup_id == powerup_id,
                PowerUpRestriction.bet_context_id == bet_context_id,
                PowerUpRestriction.event_session_id == event_session_id,
                PowerUpRestriction.testing_event_session_id == testing_event_session_id,
                PowerUpRestriction.is_disabled.is_(True),
            )
        ).first() is not None

    def _powerup_already_used(
        self,
        *,
        group_id: int,
        user_id: int,
        bet_context_id: int,
        powerup_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        return self._session.execute(
            select(PowerUpUse.id).where(
                PowerUpUse.group_id == group_id,
                PowerUpUse.user_id == user_id,
                PowerUpUse.bet_context_id == bet_context_id,
                PowerUpUse.powerup_id == powerup_id,
                PowerUpUse.event_session_id == event_session_id,
                PowerUpUse.testing_event_session_id == testing_event_session_id,
            )
        ).first() is not None

    def list_group_user_targets(
        self,
        *,
        group_id: int,
        actor_user_id: int,
    ) -> list[BetPowerUpTargetUserDefinition]:
        rows = self._session.execute(
            select(User.id, User.public_id, User.username)
            .join(GroupMembership, GroupMembership.user_id == User.id)
            .where(
                GroupMembership.group_id == group_id,
                User.id != actor_user_id,
            )
            .order_by(User.username.asc(), User.id.asc())
        ).all()

        return [
            BetPowerUpTargetUserDefinition(
                user_id=row.id,
                user_public_id=row.public_id,
                username=row.username,
            )
            for row in rows
        ]
    
    def list_group_team_targets(
        self,
        *,
        group_id: int,
    ) -> list[BetPowerUpTargetTeamDefinition]:
        rows = self._session.execute(
            select(Team.id, Team.public_id, Team.name)
            .where(Team.group_id == group_id)
            .order_by(Team.name.asc(), Team.id.asc())
        ).all()

        return [
            BetPowerUpTargetTeamDefinition(
                team_id=row.id,
                team_public_id=row.public_id,
                name=row.name,
            )
            for row in rows
        ]
    
    def count_distinct_contexts_where_user_received_powerup(
        self,
        *,
        group_id: int,
        target_user_id: int,
        powerup_id: int,
        excluding_bet_context_id: int,
    ) -> int:
        return self._session.scalar(
            select(func.count(func.distinct(PowerUpUse.bet_context_id)))
            .join(PowerUpUseTarget, PowerUpUseTarget.powerup_use_id == PowerUpUse.id)
            .where(
                PowerUpUse.group_id == group_id,
                PowerUpUse.powerup_id == powerup_id,
                PowerUpUseTarget.target_user_id == target_user_id,
                PowerUpUse.bet_context_id != excluding_bet_context_id,
            )
        ) or 0
