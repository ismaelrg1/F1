from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.auth import User
from app.db.betting import Bet, BetContext, BetPick, BetResultsVisibilityPolicy
from app.db.competition import EventSession, RaceEvent
from app.db.enums import BetContextKind, BetResultsVisibilityMode, ScoreComponentType
from app.db.scoring import OfficialResult, ResultPublication, Score, ScoreComponent, ScoreSession, ScoreSessionComponent
from app.db.social import GroupMembership
from app.domain.bets.results.models import (
    BetOfficialResult,
    BetResultAnswer,
    BetResultEntry,
    BetResultScore,
    BetResultsComponent,
    BetResultsPoints,
    BetResultsUser,
    BetResultsVisibility,
)
from app.domain.bets.results.ports import BetResultsRepository
from app.domain.bets.shared.models import (
    BetContextDefinition,
    BetExceptionDefinition,
    BetRaceEvent,
    BetRaceEventSession,
)
from app.adapters.sqlalchemy.bets.questions_repository import SqlAlchemyBetQuestionsRepository


class SqlAlchemyBetResultsRepository(BetResultsRepository):
    def __init__(self, session: Session):
        self._session = session
        self._questions_repository = SqlAlchemyBetQuestionsRepository(session)

    def get_race_event_by_public_id(self, public_id: UUID) -> BetRaceEvent | None:
        return self._questions_repository.get_race_event_by_public_id(public_id)

    def get_gp_bet_context(self, *, group_id: int, race_event_id: int) -> BetContextDefinition | None:
        return self._questions_repository.get_gp_bet_context(
            group_id=group_id,
            race_event_id=race_event_id,
        )

    def get_race_event_visibility(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        now: datetime,
    ) -> BetResultsVisibility:
        policy_stmt = (
            select(BetResultsVisibilityPolicy)
            .where(
                BetResultsVisibilityPolicy.bet_context_id == bet_context_id,
                BetResultsVisibilityPolicy.testing_event_session_id.is_(None),
                BetResultsVisibilityPolicy.starts_at.is_(None)
                | (BetResultsVisibilityPolicy.starts_at <= now),
                BetResultsVisibilityPolicy.ends_at.is_(None)
                | (BetResultsVisibilityPolicy.ends_at > now),
            )
        )

        if event_session_id is None:
            policy_stmt = policy_stmt.where(BetResultsVisibilityPolicy.event_session_id.is_(None))
        else:
            policy_stmt = policy_stmt.where(BetResultsVisibilityPolicy.event_session_id == event_session_id)

        policy = self._session.execute(policy_stmt).scalar_one_or_none()

        if policy is None and event_session_id is not None:
            fallback_stmt = (
                select(BetResultsVisibilityPolicy)
                .where(
                    BetResultsVisibilityPolicy.bet_context_id == bet_context_id,
                    BetResultsVisibilityPolicy.event_session_id.is_(None),
                    BetResultsVisibilityPolicy.testing_event_session_id.is_(None),
                    BetResultsVisibilityPolicy.starts_at.is_(None)
                    | (BetResultsVisibilityPolicy.starts_at <= now),
                    BetResultsVisibilityPolicy.ends_at.is_(None)
                    | (BetResultsVisibilityPolicy.ends_at > now),
                )
            )
            policy = self._session.execute(fallback_stmt).scalar_one_or_none()

        publication_stmt = (
            select(ResultPublication)
            .where(
                ResultPublication.bet_context_id == bet_context_id,
                ResultPublication.testing_event_session_id.is_(None),
            )
        )

        if event_session_id is None:
            publication_stmt = publication_stmt.where(ResultPublication.event_session_id.is_(None))
        else:
            publication_stmt = publication_stmt.where(ResultPublication.event_session_id == event_session_id)

        publication = self._session.execute(publication_stmt).scalar_one_or_none()

        return BetResultsVisibility(
            mode=(
                policy.visibility_mode
                if policy is not None
                else BetResultsVisibilityMode.SUBMIT_REQUIRED
            ),
            can_view_group_results=False,
            reason="PENDING",
            is_locked=False,
            results_published=publication is not None,
            results_published_at=publication.published_at if publication is not None else None,
            viewer_submitted=False,
        )

    def viewer_has_submitted_scope(
        self,
        *,
        user_id: int,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> bool:
        stmt = (
            select(Bet.id)
            .where(
                Bet.user_id == user_id,
                Bet.bet_context_id == bet_context_id,
                Bet.testing_event_session_id.is_(None),
                Bet.submitted_at.is_not(None),
            )
        )

        if event_session_id is None:
            stmt = stmt.where(Bet.event_session_id.is_(None))
        else:
            stmt = stmt.where(Bet.event_session_id == event_session_id)

        return self._session.execute(stmt).first() is not None

    def list_official_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> list[BetOfficialResult]:
        stmt = (
            select(OfficialResult)
            .where(
                OfficialResult.bet_context_id == bet_context_id,
                OfficialResult.testing_event_session_id.is_(None),
            )
            .options(joinedload(OfficialResult.bet_score))
        )

        if event_session_id is None:
            stmt = stmt.where(OfficialResult.event_session_id.is_(None))
        else:
            stmt = stmt.where(OfficialResult.event_session_id == event_session_id)

        results = self._session.execute(stmt).scalars().all()

        return [
            BetOfficialResult(
                bet_score_code=result.bet_score.code,
                label=result.bet_score.label,
                value=result.value,
                source=result.source.value,
                created_at=result.created_at,
            )
            for result in sorted(results, key=lambda item: item.bet_score.code)
        ]

    def list_group_submitted_bet_entries(
        self,
        *,
        group_id: int,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> list[BetResultEntry]:
        bets = self._list_scope_bets(
            group_id=group_id,
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
        )
        official_values_by_score_id = self._official_values_by_score_id(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
        )
        score_components_by_user_id, scores_by_user_id = self._score_data_by_user_id(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
        )

        entries: list[BetResultEntry] = []
        for bet in bets:
            components = score_components_by_user_id.get(bet.user_id, [])
            question_components_by_score_code, score_level_components = self._split_components_by_question(components)

            answers = [
                self._map_answer(
                    pick=pick,
                    official_values_by_score_id=official_values_by_score_id,
                    components=question_components_by_score_code.get(pick.bet_score.code, []),
                )
                for pick in sorted(bet.bet_picks, key=lambda item: (item.bet_score.code, item.id))
            ]

            score = scores_by_user_id.get(bet.user_id)
            entries.append(
                BetResultEntry(
                    user=BetResultsUser(
                        public_id=bet.user.public_id,
                        username=bet.user.username,
                        display_name=getattr(bet.user, "display_name", None),
                    ),
                    submitted_at=bet.submitted_at,
                    last_modified_at=bet.last_modified_at,
                    locked_at=bet.locked_at,
                    answers=answers,
                    score=(
                        BetResultScore(
                            points=self._sum_points(components),
                            components=score_level_components,
                            computed_at=score.computed_at,
                        )
                        if score is not None
                        else None
                    ),
                )
            )

        return entries

    def _list_scope_bets(
        self,
        *,
        group_id: int,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> list[Bet]:
        user_ids_stmt = (
            select(GroupMembership.user_id)
            .where(GroupMembership.group_id == group_id)
        )

        stmt = (
            select(Bet)
            .where(
                Bet.user_id.in_(user_ids_stmt),
                Bet.bet_context_id == bet_context_id,
                Bet.testing_event_session_id.is_(None),
                Bet.submitted_at.is_not(None),
            )
            .options(
                joinedload(Bet.user),
                selectinload(Bet.bet_picks).joinedload(BetPick.bet_score),
            )
        )

        if event_session_id is None:
            stmt = stmt.where(Bet.event_session_id.is_(None))
        else:
            stmt = stmt.where(Bet.event_session_id == event_session_id)

        return list(self._session.execute(stmt).scalars().unique().all())

    def _official_values_by_score_id(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> dict[int, str]:
        stmt = (
            select(OfficialResult)
            .where(
                OfficialResult.bet_context_id == bet_context_id,
                OfficialResult.testing_event_session_id.is_(None),
            )
        )

        if event_session_id is None:
            stmt = stmt.where(OfficialResult.event_session_id.is_(None))
        else:
            stmt = stmt.where(OfficialResult.event_session_id == event_session_id)

        results = self._session.execute(stmt).scalars().all()
        return {result.bet_score_id: result.value for result in results}

    def _score_data_by_user_id(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
    ) -> tuple[dict[int, list[BetResultsComponent]], dict[int, Score | ScoreSession]]:
        if event_session_id is None:
            stmt = (
                select(Score)
                .where(Score.bet_context_id == bet_context_id)
                .options(selectinload(Score.score_components))
            )
            scores = list(self._session.execute(stmt).scalars().unique().all())
            return (
                {
                    score.user_id: [
                        self._map_component(component)
                        for component in score.score_components
                    ]
                    for score in scores
                },
                {score.user_id: score for score in scores},
            )

        stmt = (
            select(ScoreSession)
            .where(
                ScoreSession.bet_context_id == bet_context_id,
                ScoreSession.event_session_id == event_session_id,
            )
            .options(selectinload(ScoreSession.score_session_components))
        )
        scores = list(self._session.execute(stmt).scalars().unique().all())

        return (
            {
                score.user_id: [
                    self._map_session_component(component)
                    for component in score.score_session_components
                ]
                for score in scores
            },
            {score.user_id: score for score in scores},
        )

    def _split_components_by_question(
        self,
        components: list[BetResultsComponent],
    ) -> tuple[dict[str, list[BetResultsComponent]], list[BetResultsComponent]]:
        question_components_by_code: dict[str, list[BetResultsComponent]] = defaultdict(list)
        score_level_components: list[BetResultsComponent] = []

        for component in components:
            applies_to = component.applies_to or {}
            bet_score_code = applies_to.get("bet_score_code")

            if applies_to.get("level") == "QUESTION" and bet_score_code is not None:
                question_components_by_code[str(bet_score_code)].append(component)
            else:
                score_level_components.append(component)

        return question_components_by_code, score_level_components

    def _map_answer(
        self,
        *,
        pick: BetPick,
        official_values_by_score_id: dict[int, str],
        components: list[BetResultsComponent],
    ) -> BetResultAnswer:
        official_value = official_values_by_score_id.get(pick.bet_score_id)

        return BetResultAnswer(
            bet_score_code=pick.bet_score.code,
            label=pick.bet_score.label,
            value=pick.value,
            is_invalid=pick.is_invalid,
            invalid_reason=pick.invalid_reason,
            official_value=official_value,
            is_correct=None if official_value is None else pick.value == official_value,
            points=self._sum_points(components),
            components=components,
        )

    def _map_component(self, component: ScoreComponent) -> BetResultsComponent:
        return BetResultsComponent(
            type=component.component_type,
            code=component.code,
            points=float(component.points),
            applies_to=self._extract_applies_to(component.details_json),
            details=component.details_json,
        )

    def _map_session_component(self, component: ScoreSessionComponent) -> BetResultsComponent:
        return BetResultsComponent(
            type=component.component_type,
            code=component.code,
            points=float(component.points),
            applies_to=self._extract_applies_to(component.details_json),
            details=component.details_json,
        )

    def _extract_applies_to(self, details: dict[str, Any] | None) -> dict[str, Any] | None:
        if not details:
            return None

        applies_to = details.get("applies_to")
        if isinstance(applies_to, dict):
            return applies_to

        bet_score_code = details.get("bet_score_code")
        if bet_score_code is not None:
            return {
                "level": "QUESTION",
                "bet_score_code": bet_score_code,
            }

        return None

    def _sum_points(self, components: list[BetResultsComponent]) -> BetResultsPoints:
        base = sum(component.points for component in components if component.type == ScoreComponentType.BASE)
        powerup = sum(component.points for component in components if component.type == ScoreComponentType.POWERUP)
        extra = sum(component.points for component in components if component.type == ScoreComponentType.EXTRA)
        penalty = sum(component.points for component in components if component.type == ScoreComponentType.PENALTY)

        return BetResultsPoints(
            base=base,
            powerup=powerup,
            extra=extra,
            penalty=penalty,
            total=base + powerup + extra - penalty,
        )