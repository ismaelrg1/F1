from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import joinedload, selectinload


from app.adapters.sqlalchemy.bets.base_repository import SqlAlchemyBetBaseRepository
from app.db.auth import User
from app.db.powerups import PowerUp, PowerUpAssignment, PowerUpRestriction, PowerUpUse, PowerUpUseTarget
from app.db.social import Group, Team
from app.db.enums import PowerUpTargetMode, PowerUpTargetType
from app.db.betting import Bet, BetContext, BetEditPermission, BetPick, BetScore, BetSubmissionRevision, BetScoreRelation
from app.domain.bets.models import (
    BetAnswerInput,
    BetAnswerResult,
    BetEditPermissionDefinition,
    BetScoreRelationDefinition,
    UserBetDefinition,
)
from app.domain.bets.answers.models import (
    BetPowerUpAssignmentDefinition,
    ResolvedBetPowerUpUse,
)
from app.domain.bets.ports import BetAnswersRepository


class SqlAlchemyBetAnswersRepository(SqlAlchemyBetBaseRepository, BetAnswersRepository):
    def list_user_bets_for_context(
        self,
        *,
        user_id: int,
        bet_context_id: int,
    ) -> list[UserBetDefinition]:
        stmt = (
            select(Bet)
            .where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
            )
            .options(
                selectinload(Bet.bet_picks).joinedload(BetPick.bet_score),
                selectinload(Bet.submission_revisions),
            )
        )
        bets = self._session.execute(stmt).scalars().unique().all()

        return [
            UserBetDefinition(
                event_session_id=bet.event_session_id,
                testing_event_session_id=getattr(bet, "testing_event_session_id", None),
                submitted_at=bet.submitted_at,
                last_modified_at=bet.last_modified_at,
                locked_at=bet.locked_at,
                picks=tuple(
                    BetAnswerResult(
                        bet_score_code=pick.bet_score.code,
                        value=pick.value,
                    )
                    for pick in sorted(bet.bet_picks, key=lambda p: (p.bet_score.code, p.id))
                ),
                revision_count=len(bet.submission_revisions),
            )
            for bet in bets
        ]

    def list_bet_score_relations_for_codes(
        self,
        *,
        codes: set[str],
    ) -> list[BetScoreRelationDefinition]:
        if not codes:
            return []

        stmt = (
            select(BetScoreRelation)
            .join(
                BetScore,
                BetScore.id == BetScoreRelation.source_bet_score_id,
            )
            .where(BetScore.code.in_(codes))
            .options(
                joinedload(BetScoreRelation.source_bet_score),
                joinedload(BetScoreRelation.target_bet_score),
            )
        )

        relations = self._session.execute(stmt).scalars().unique().all()

        return [
            BetScoreRelationDefinition(
                source_bet_score_code=relation.source_bet_score.code,
                target_bet_score_code=relation.target_bet_score.code,
                relation_type=relation.relation_type.value,
                config_json=relation.config_json,
            )
            for relation in relations
            if relation.target_bet_score.code in codes
        ]

    def get_bet_score_ids_by_codes(self, *, codes: set[str]) -> dict[str, int]:
        if not codes:
            return {}

        stmt = select(BetScore).where(BetScore.code.in_(codes))
        scores = self._session.execute(stmt).scalars().all()

        return {
            score.code: score.id
            for score in scores
        }

    def upsert_user_bet_draft(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        answers: list[BetAnswerInput],
        modified_at: datetime,
    ) -> None:
        stmt = (
            select(Bet)
            .where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
                Bet.event_session_id.is_(None)
                if event_session_id is None
                else Bet.event_session_id == event_session_id,
                Bet.testing_event_session_id.is_(None)
                if testing_event_session_id is None
                else Bet.testing_event_session_id == testing_event_session_id,
            )
            .options(selectinload(Bet.bet_picks))
        )
        bet = self._session.execute(stmt).scalar_one_or_none()

        if bet is None:
            bet = Bet(
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
                submitted_at=None,
                last_modified_at=modified_at,
                locked_at=None,
            )
            self._session.add(bet)
            self._session.flush()
        else:
            bet.submitted_at = None
            bet.last_modified_at = modified_at
            bet.locked_at = None

        score_ids_by_code = self.get_bet_score_ids_by_codes(
            codes={answer.bet_score_code for answer in answers},
        )

        existing_picks_by_score_id = {
            pick.bet_score_id: pick
            for pick in bet.bet_picks
        }

        for answer in answers:
            bet_score_id = score_ids_by_code[answer.bet_score_code]
            existing_pick = existing_picks_by_score_id.get(bet_score_id)

            if existing_pick is None:
                self._session.add(
                    BetPick(
                        bet_id=bet.id,
                        bet_score_id=bet_score_id,
                        value=answer.value,
                    )
                )
            else:
                existing_pick.value = answer.value

        self._session.flush()

    def list_active_edit_permissions_for_scope(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        now: datetime,
    ) -> list[BetEditPermissionDefinition]:
        stmt = select(BetEditPermission).where(
            BetEditPermission.bet_context_id == bet_context_id,
            BetEditPermission.starts_at <= now,
            BetEditPermission.ends_at > now,
            BetEditPermission.event_session_id.is_(None)
            if event_session_id is None
            else BetEditPermission.event_session_id == event_session_id,
            BetEditPermission.testing_event_session_id.is_(None)
            if testing_event_session_id is None
            else BetEditPermission.testing_event_session_id == testing_event_session_id,
        )

        permissions = self._session.execute(stmt).scalars().all()

        return [
            BetEditPermissionDefinition(
                applies_to_all=permission.applies_to_all,
                group_id=permission.group_id,
                user_id=permission.user_id,
                team_id=permission.team_id,
                starts_at=permission.starts_at,
                ends_at=permission.ends_at,
                max_modifications=permission.max_modifications,
            )
            for permission in permissions
        ]

    def upsert_user_bet_submission(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        answers: list[BetAnswerInput],
        submitted_at: datetime,
    ) -> None:
        stmt = (
            select(Bet)
            .where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
                Bet.event_session_id.is_(None)
                if event_session_id is None
                else Bet.event_session_id == event_session_id,
                Bet.testing_event_session_id.is_(None)
                if testing_event_session_id is None
                else Bet.testing_event_session_id == testing_event_session_id,
            )
            .options(
                selectinload(Bet.bet_picks),
                selectinload(Bet.submission_revisions),
            )
        )
        bet = self._session.execute(stmt).scalar_one_or_none()

        if bet is None:
            bet = Bet(
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
                submitted_at=submitted_at,
                last_modified_at=submitted_at,
                locked_at=None,
                submit_order_int=None,
            )
            self._session.add(bet)
            self._session.flush()
        else:
            if bet.submitted_at is None:
                bet.submitted_at = submitted_at

            bet.last_modified_at = submitted_at
            bet.locked_at = None
            bet.submit_order_int = None

        score_ids_by_code = self.get_bet_score_ids_by_codes(
            codes={answer.bet_score_code for answer in answers},
        )

        existing_picks_by_score_id = {
            pick.bet_score_id: pick
            for pick in bet.bet_picks
        }

        for answer in answers:
            bet_score_id = score_ids_by_code[answer.bet_score_code]
            existing_pick = existing_picks_by_score_id.get(bet_score_id)

            if existing_pick is None:
                self._session.add(
                    BetPick(
                        bet_id=bet.id,
                        bet_score_id=bet_score_id,
                        value=answer.value,
                    )
                )
            else:
                existing_pick.value = answer.value

        next_revision_number = len(bet.submission_revisions) + 1

        self._session.add(
            BetSubmissionRevision(
                bet_id=bet.id,
                revision_number=next_revision_number,
                submitted_at=submitted_at,
                reason=None,
            )
        )

        self._session.flush()
        self._session.expire(bet, ["bet_picks", "submission_revisions"])

    def get_powerup_assignment_for_submission(
        self,
        *,
        group_id: int,
        user_id: int,
        bet_context_id: int,
        powerup_code: str,
    ) -> BetPowerUpAssignmentDefinition | None:
        bet_context = self._session.scalar(
            select(BetContext).where(BetContext.id == bet_context_id)
        )
        if bet_context is None:
            return None

        assignments = self._session.scalars(
            select(PowerUpAssignment)
            .join(PowerUp, PowerUp.id == PowerUpAssignment.powerup_id)
            .where(
                PowerUpAssignment.group_id == group_id,
                PowerUpAssignment.user_id == user_id,
                PowerUpAssignment.is_active.is_(True),
                PowerUp.code == powerup_code,
                or_(
                    PowerUpAssignment.bet_context_id == bet_context_id,
                    and_(
                        PowerUpAssignment.season_id == bet_context.season_id,
                        PowerUpAssignment.bet_context_id.is_(None),
                    ),
                ),
            )
            .options(joinedload(PowerUpAssignment.powerup))
        ).all()

        if not assignments:
            return None

        assignment = next(
            (item for item in assignments if item.bet_context_id == bet_context_id),
            assignments[0],
        )

        return BetPowerUpAssignmentDefinition(
            powerup_id=assignment.powerup_id,
            code=assignment.powerup.code,
            name=assignment.powerup.name,
            is_enabled=assignment.powerup.is_enabled,
            target_mode=assignment.powerup.target_mode.value,
            quantity=assignment.quantity,
        )

    def user_has_any_submitted_bet_for_context(
        self,
        *,
        user_id: int,
        bet_context_id: int,
    ) -> bool:
        return self._session.execute(
            select(Bet.id).where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
                Bet.submitted_at.is_not(None),
            )
        ).first() is not None

    def powerup_already_used(
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

    def powerup_is_restricted(
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

    def get_user_id_by_public_id(self, public_id: UUID) -> int | None:
        return self._session.scalar(
            select(User.id).where(User.public_id == public_id)
        )

    def get_team_id_by_public_id(self, public_id: UUID) -> int | None:
        return self._session.scalar(
            select(Team.id).where(Team.public_id == public_id)
        )

    def get_group_id_by_public_id(self, public_id: UUID) -> int | None:
        return self._session.scalar(
            select(Group.id).where(Group.public_id == public_id)
        )

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

    def create_powerup_uses_for_submission(
        self,
        *,
        group_id: int,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        powerups: list[ResolvedBetPowerUpUse],
    ) -> None:
        for requested in powerups:
            use = PowerUpUse(
                group_id=group_id,
                user_id=user_id,
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
                powerup_id=requested.powerup_id,
                rule_json=requested.rule_json,
            )
            self._session.add(use)
            self._session.flush()

            for target in requested.targets:
                self._session.add(
                    PowerUpUseTarget(
                        powerup_use_id=use.id,
                        target_type=target.target_type,
                        target_user_id=target.target_user_id,
                        target_team_id=target.target_team_id,
                        target_group_id=target.target_group_id,
                        rule_json=target.rule_json,
                    )
                )

            bet_context = self._session.scalar(
                select(BetContext).where(BetContext.id == bet_context_id)
            )

            assignment = None
            if bet_context is not None:
                assignment = self._session.scalar(
                    select(PowerUpAssignment)
                    .where(
                        PowerUpAssignment.group_id == group_id,
                        PowerUpAssignment.user_id == user_id,
                        PowerUpAssignment.powerup_id == requested.powerup_id,
                        PowerUpAssignment.is_active.is_(True),
                        or_(
                            PowerUpAssignment.bet_context_id == bet_context_id,
                            and_(
                                PowerUpAssignment.season_id == bet_context.season_id,
                                PowerUpAssignment.bet_context_id.is_(None),
                            ),
                        ),
                    )
                    .order_by(PowerUpAssignment.bet_context_id.is_(None).asc())
                )

            if assignment is not None:
                assignment.quantity -= 1

        self._session.flush()
