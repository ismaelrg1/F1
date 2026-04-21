from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.adapters.sqlalchemy.bets.base_repository import SqlAlchemyBetBaseRepository
from app.db.betting import Bet, BetEditPermission, BetPick, BetScore, BetSubmissionRevision
from app.domain.bets.models import (
    BetAnswerInput,
    BetAnswerResult,
    BetEditPermissionDefinition,
    UserBetDefinition,
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
