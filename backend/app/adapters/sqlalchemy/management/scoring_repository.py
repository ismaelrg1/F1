from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.db.betting import Bet, BetContext, BetPick
from app.db.competition import EventSession, RaceEvent, Season, TestingEvent, TestingEventSession
from app.db.enums import BetContextKind, ScoreComponentType
from app.db.scoring import (
    OfficialResult,
    Score,
    ScoreComponent,
    ScoreSession,
    ScoreSessionComponent,
)
from app.domain.management.scoring.evaluators import BaseEvaluator
from app.domain.management.scoring.models import (
    ScoringCalculationResult,
    ScoringScope,
)


class SqlAlchemyManagementScoringRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_race_event_scope(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
    ) -> ScoringScope | None:
        row = self._session.execute(
            select(BetContext, RaceEvent)
            .join(RaceEvent, RaceEvent.id == BetContext.race_event_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.GP,
                RaceEvent.public_id == race_event_public_id,
            )
        ).first()
        if row is None:
            return None

        bet_context, race_event = row

        event_session_ids = tuple(
            self._session.scalars(
                select(EventSession.id).where(EventSession.race_event_id == race_event.id)
            ).all()
        )

        return ScoringScope(
            group_id=group_id,
            season_id=bet_context.season_id,
            bet_context_id=bet_context.id,
            race_event_id=race_event.id,
            event_session_ids=event_session_ids,
        )

    def get_testing_event_scope(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
    ) -> ScoringScope | None:
        row = self._session.execute(
            select(BetContext, TestingEvent)
            .join(TestingEvent, TestingEvent.id == BetContext.testing_event_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.PRETESTING,
                TestingEvent.public_id == testing_event_public_id,
            )
        ).first()
        if row is None:
            return None

        bet_context, testing_event = row

        testing_event_session_ids = tuple(
            self._session.scalars(
                select(TestingEventSession.id).where(
                    TestingEventSession.testing_event_id == testing_event.id
                )
            ).all()
        )

        return ScoringScope(
            group_id=group_id,
            season_id=bet_context.season_id,
            bet_context_id=bet_context.id,
            testing_event_id=testing_event.id,
            testing_event_session_ids=testing_event_session_ids,
        )

    def get_season_scope(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> ScoringScope | None:
        row = self._session.execute(
            select(BetContext, Season)
            .join(Season, Season.id == BetContext.season_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.SEASON,
                BetContext.race_event_id.is_(None),
                BetContext.testing_event_id.is_(None),
                Season.year == season_year,
            )
        ).first()
        if row is None:
            return None

        bet_context, season = row

        return ScoringScope(
            group_id=group_id,
            season_id=season.id,
            bet_context_id=bet_context.id,
        )

    def official_results_exist(self, scope: ScoringScope) -> bool:
        stmt = select(OfficialResult.id).where(
            OfficialResult.bet_context_id == scope.bet_context_id,
        )
        return self._session.execute(stmt).first() is not None

    def delete_existing_scores(self, scope: ScoringScope) -> None:
        score_ids = self._session.scalars(
            select(Score.id).where(Score.bet_context_id == scope.bet_context_id)
        ).all()
        if score_ids:
            self._session.execute(
                delete(ScoreComponent).where(ScoreComponent.score_id.in_(score_ids))
            )
            self._session.execute(
                delete(Score).where(Score.id.in_(score_ids))
            )

        score_session_ids = self._session.scalars(
            select(ScoreSession.id).where(ScoreSession.bet_context_id == scope.bet_context_id)
        ).all()
        if score_session_ids:
            self._session.execute(
                delete(ScoreSessionComponent).where(
                    ScoreSessionComponent.score_session_id.in_(score_session_ids)
                )
            )
            self._session.execute(
                delete(ScoreSession).where(ScoreSession.id.in_(score_session_ids))
            )

        self._session.flush()

    def calculate_scores(self, scope: ScoringScope) -> ScoringCalculationResult:
        official_results = self._load_official_results(scope)

        bets = self._session.scalars(
            select(Bet)
            .where(
                Bet.bet_context_id == scope.bet_context_id,
                Bet.submitted_at.is_not(None),
            )
            .options(
                joinedload(Bet.bet_picks).joinedload(BetPick.bet_score),
            )
        ).unique().all()

        calculated_users: set[int] = set()
        score_components_count = 0
        score_session_components_count = 0

        for bet in bets:
            picks = [pick for pick in bet.bet_picks if not pick.is_invalid]
            if not picks:
                continue

            calculated_users.add(bet.user_id)

            if bet.event_session_id is not None or bet.testing_event_session_id is not None:
                row, components_count = self._calculate_session_bet(
                    bet=bet,
                    picks=picks,
                    official_results=official_results,
                    scope=scope,
                )
                score_session_components_count += components_count
            else:
                row, components_count = self._calculate_context_bet(
                    bet=bet,
                    picks=picks,
                    official_results=official_results,
                    scope=scope,
                )
                score_components_count += components_count

        self._session.flush()

        return ScoringCalculationResult(
            calculated=True,
            calculated_users=len(calculated_users),
            score_components_count=score_components_count,
            score_session_components_count=score_session_components_count,
            computed_at=datetime.now(timezone.utc),
        )

    def recalculate_season_aggregates(self, scope: ScoringScope) -> None:
        return None

    def _calculate_context_bet(self, *, bet: Bet, picks: list[BetPick], official_results: dict, scope: ScoringScope):
        score = Score(
            user_id=bet.user_id,
            bet_context_id=scope.bet_context_id,
            base_points=Decimal("0"),
            total_points=Decimal("0"),
        )
        self._session.add(score)
        self._session.flush()

        total = Decimal("0")
        components_count = 0

        for pick in picks:
            result = self._evaluate_pick(bet=bet, pick=pick, official_results=official_results)
            if result is None:
                continue

            evaluation, official_result = result
            total += evaluation.points

            self._session.add(
                ScoreComponent(
                    score_id=score.id,
                    component_type=ScoreComponentType.BASE,
                    code=pick.bet_score.code,
                    points=evaluation.points,
                    details_json={
                        **evaluation.details,
                        "bet_score_id": pick.bet_score_id,
                        "bet_pick_id": pick.id,
                        "official_result_id": official_result.id,
                    },
                )
            )
            components_count += 1

        score.base_points = total
        score.total_points = total

        return score, components_count

    def _calculate_session_bet(self, *, bet: Bet, picks: list[BetPick], official_results: dict, scope: ScoringScope):
        score_session = ScoreSession(
            user_id=bet.user_id,
            bet_context_id=scope.bet_context_id,
            event_session_id=bet.event_session_id,
            testing_event_session_id=bet.testing_event_session_id,
            base_points=Decimal("0"),
            total_points=Decimal("0"),
        )
        self._session.add(score_session)
        self._session.flush()

        total = Decimal("0")
        components_count = 0

        for pick in picks:
            result = self._evaluate_pick(bet=bet, pick=pick, official_results=official_results)
            if result is None:
                continue

            evaluation, official_result = result
            total += evaluation.points

            self._session.add(
                ScoreSessionComponent(
                    score_session_id=score_session.id,
                    component_type=ScoreComponentType.BASE,
                    code=pick.bet_score.code,
                    points=evaluation.points,
                    details_json={
                        **evaluation.details,
                        "bet_score_id": pick.bet_score_id,
                        "bet_pick_id": pick.id,
                        "official_result_id": official_result.id,
                    },
                )
            )
            components_count += 1

        score_session.base_points = total
        score_session.total_points = total

        return score_session, components_count

    def _evaluate_pick(self, *, bet: Bet, pick: BetPick, official_results: dict):
        official_result = official_results.get(
            (
                pick.bet_score_id,
                bet.event_session_id,
                bet.testing_event_session_id,
            )
        )
        if official_result is None:
            return None

        evaluator = BaseEvaluator.get("exact_match")
        evaluation = evaluator.evaluate(
            pick=pick,
            official_result=official_result,
            bet_score=pick.bet_score,
            rule=None,
        )

        return evaluation, official_result

    def _load_official_results(self, scope: ScoringScope) -> dict:
        rows = self._session.scalars(
            select(OfficialResult).where(
                OfficialResult.bet_context_id == scope.bet_context_id,
            )
        ).all()

        return {
            (
                row.bet_score_id,
                row.event_session_id,
                row.testing_event_session_id,
            ): row
            for row in rows
        }