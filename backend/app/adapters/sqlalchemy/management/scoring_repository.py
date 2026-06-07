from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.db.betting import Bet, BetContext, BetPick, BetScoreRelation
from app.db.powerups import PowerUpUse, PowerUpRestriction
from app.db.competition import EventSession, RaceEvent, Season, TestingEvent, TestingEventSession
from app.db.enums import (
    BetContextKind, 
    ScoreComponentType,
    ScoringRuleScope,
)
from app.db.scoring import (
    OfficialResult,
    Score,
    ScoreComponent,
    ScoreSession,
    ScoreSessionComponent,
    ScoringRule
)
from app.db.social import GroupMembership
from app.domain.management.scoring.evaluators import BaseEvaluator
from app.domain.management.scoring.models import (
    ScoringCalculationResult,
    ScoringScope,
    PowerUpEvaluationContext,
)
from app.domain.management.scoring.powerups import BasePowerUpEvaluator

from app.domain.management.scoring.ports import ManagementScoringRepository


class SqlAlchemyManagementScoringRepository(ManagementScoringRepository):
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
        return (
            self._session.execute(
                select(OfficialResult.id).where(
                    OfficialResult.bet_context_id == scope.bet_context_id,
                )
            ).first()
            is not None
        )

    def delete_existing_scores(self, scope: ScoringScope) -> None:
        score_ids = self._session.scalars(
            select(Score.id).where(Score.bet_context_id == scope.bet_context_id)
        ).all()
        if score_ids:
            self._session.execute(
                delete(ScoreComponent).where(ScoreComponent.score_id.in_(score_ids))
            )
            self._session.execute(delete(Score).where(Score.id.in_(score_ids)))

        score_session_ids = self._session.scalars(
            select(ScoreSession.id).where(
                ScoreSession.bet_context_id == scope.bet_context_id
            )
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
        rules = self._load_rules(scope)
        relations_by_source = self._load_relations_by_source()
        powerup_uses = self._load_powerup_uses(scope)
        powerup_restrictions = self._load_powerup_restrictions(scope)
        bets = self._load_submitted_bets(scope)

        calculated_users: set[int] = set()
        score_components_count = 0
        score_session_components_count = 0

        scores_by_user: dict[int, Score] = {}
        score_sessions_by_key: dict[tuple[int, int | None, int | None], ScoreSession] = {}

        for bet in bets:
            picks = [pick for pick in bet.bet_picks if not pick.is_invalid]
            if not picks:
                continue

            calculated_users.add(bet.user_id)

            if bet.event_session_id is not None or bet.testing_event_session_id is not None:
                score_session, count = self._calculate_session_bet(
                    bet=bet,
                    picks=picks,
                    official_results=official_results,
                    rules=rules,
                    relations_by_source=relations_by_source,
                )
                score_sessions_by_key[
                    (bet.user_id, bet.event_session_id, bet.testing_event_session_id)
                ] = score_session
                score_session_components_count += count
            else:
                score, count = self._calculate_context_bet(
                    bet=bet,
                    picks=picks,
                    official_results=official_results,
                    rules=rules,
                    relations_by_source=relations_by_source,
                )
                scores_by_user[bet.user_id] = score
                score_components_count += count

        score_components_count += self._apply_context_powerups(
            powerup_uses=powerup_uses,
            powerup_restrictions=powerup_restrictions,
            scores_by_user=scores_by_user,
        )
        score_session_components_count += self._apply_session_powerups(
            powerup_uses=powerup_uses,
            powerup_restrictions=powerup_restrictions,
            score_sessions_by_key=score_sessions_by_key,
        )

        self._session.flush()

        return ScoringCalculationResult(
            calculated=True,
            calculated_users=len(calculated_users),
            score_components_count=score_components_count,
            score_session_components_count=score_session_components_count,
            computed_at=datetime.now(timezone.utc),
        )

    def _calculate_context_bet(
        self,
        *,
        bet: Bet,
        picks: list[BetPick],
        official_results: dict,
        rules: list[ScoringRule],
        relations_by_source: dict[int, list[BetScoreRelation]],
    ) -> tuple[Score, int]:
        score = Score(
            user_id=bet.user_id,
            bet_context_id=bet.bet_context_id,
            base_points=Decimal("0"),
            total_points=Decimal("0"),
        )
        self._session.add(score)
        self._session.flush()

        picks_by_score_id = {pick.bet_score_id: pick for pick in picks}
        hit_by_bet_score_id: dict[int, bool] = {}

        total = Decimal("0")
        hits_count = 0
        picks_count = 0
        components_count = 0

        for pick in picks:
            result = self._evaluate_pick(
                bet=bet,
                pick=pick,
                official_results=official_results,
                rules=rules,
                relations_by_source=relations_by_source,
                picks_by_score_id=picks_by_score_id,
            )
            if result is None:
                continue

            evaluation, official_result, rule = result

            total += evaluation.points
            picks_count += 1
            hit_by_bet_score_id[pick.bet_score_id] = evaluation.hit

            if evaluation.hit:
                hits_count += 1

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
                        "scoring_rule_id": rule.id if rule is not None else None,
                    },
                )
            )
            components_count += 1

        score.base_points = total
        score.total_points = total

        components_count += self._apply_extra_rules_to_score(
            score=score,
            rules=rules,
            bet_context_id=bet.bet_context_id,
            event_session_id=None,
            hits_count=hits_count,
            picks_count=picks_count,
            hit_by_bet_score_id=hit_by_bet_score_id,
        )

        return score, components_count

    def _calculate_session_bet(
        self,
        *,
        bet: Bet,
        picks: list[BetPick],
        official_results: dict,
        rules: list[ScoringRule],
        relations_by_source: dict[int, list[BetScoreRelation]],
    ) -> tuple[ScoreSession, int]:
        score_session = ScoreSession(
            user_id=bet.user_id,
            bet_context_id=bet.bet_context_id,
            event_session_id=bet.event_session_id,
            testing_event_session_id=bet.testing_event_session_id,
            base_points=Decimal("0"),
            total_points=Decimal("0"),
        )
        self._session.add(score_session)
        self._session.flush()

        picks_by_score_id = {pick.bet_score_id: pick for pick in picks}
        hit_by_bet_score_id: dict[int, bool] = {}

        total = Decimal("0")
        hits_count = 0
        picks_count = 0
        components_count = 0

        for pick in picks:
            result = self._evaluate_pick(
                bet=bet,
                pick=pick,
                official_results=official_results,
                rules=rules,
                relations_by_source=relations_by_source,
                picks_by_score_id=picks_by_score_id,
            )
            if result is None:
                continue

            evaluation, official_result, rule = result

            total += evaluation.points
            picks_count += 1
            hit_by_bet_score_id[pick.bet_score_id] = evaluation.hit

            if evaluation.hit:
                hits_count += 1

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
                        "scoring_rule_id": rule.id if rule is not None else None,
                    },
                )
            )
            components_count += 1

        score_session.base_points = total
        score_session.total_points = total

        components_count += self._apply_extra_rules_to_score_session(
            score_session=score_session,
            rules=rules,
            bet_context_id=bet.bet_context_id,
            event_session_id=bet.event_session_id,
            hits_count=hits_count,
            picks_count=picks_count,
            hit_by_bet_score_id=hit_by_bet_score_id,
        )

        return score_session, components_count

    def _evaluate_pick(
        self,
        *,
        bet: Bet,
        pick: BetPick,
        official_results: dict,
        rules: list[ScoringRule],
        relations_by_source: dict[int, list[BetScoreRelation]],
        picks_by_score_id: dict[int, BetPick],
    ):
        official_result = official_results.get(
            (
                pick.bet_score_id,
                bet.event_session_id,
                bet.testing_event_session_id,
            )
        )
        if official_result is None:
            return None

        rule = self._resolve_rule(
            rules=rules,
            component_type=ScoreComponentType.BASE,
            bet_context_id=bet.bet_context_id,
            bet_score_id=pick.bet_score_id,
            event_session_id=bet.event_session_id,
        )

        evaluator_key = rule.evaluator_key if rule is not None else "exact_match"
        evaluator = BaseEvaluator.get(evaluator_key)

        evaluation = evaluator.evaluate(
            pick=pick,
            official_result=official_result,
            bet_score=pick.bet_score,
            rule=rule,
            relations=relations_by_source.get(pick.bet_score_id, []),
            related_picks=picks_by_score_id,
        )

        return evaluation, official_result, rule
    
    def _apply_context_powerups(
        self,
        *,
        powerup_uses: list[PowerUpUse],
        powerup_restrictions: list[PowerUpRestriction],
        scores_by_user: dict[int, Score],
    ) -> int:
        count = 0
        base_points_by_user = {
            user_id: Decimal(str(score.base_points))
            for user_id, score in scores_by_user.items()
        }

        for powerup_use in powerup_uses:
            if powerup_use.event_session_id is not None:
                continue
            if powerup_use.testing_event_session_id is not None:
                continue
            if not powerup_use.powerup.is_enabled:
                continue
            if self._is_powerup_restricted(
                powerup_use=powerup_use,
                restrictions=powerup_restrictions,
            ):
                continue

            context = PowerUpEvaluationContext(
                powerup_code=powerup_use.powerup.code,
                actor_user_id=powerup_use.user_id,
                target_user_ids=self._resolve_powerup_target_user_ids(powerup_use),
                event_session_id=None,
                testing_event_session_id=None,
                base_points_by_user=base_points_by_user,
                rule_json=powerup_use.rule_json or {},
            )

            evaluator = BasePowerUpEvaluator.get(powerup_use.powerup.code)

            for effect in evaluator.evaluate(context):
                score = scores_by_user.get(effect.target_user_id)
                if score is None:
                    continue

                self._add_score_powerup_component(
                    score=score,
                    effect=effect,
                    component_code=f"{effect.code}_{powerup_use.id}",
                    powerup_use_id=powerup_use.id,
                )
                count += 1

        return count
    
    def _apply_extra_rules_to_score_session(
        self,
        *,
        score_session: ScoreSession,
        rules: list[ScoringRule],
        bet_context_id: int,
        event_session_id: int | None,
        hits_count: int,
        picks_count: int,
        hit_by_bet_score_id: dict[int, bool],
    ) -> int:
        count = 0

        for rule in self._matching_extra_rules(
            rules=rules,
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
        ):
            points = self._evaluate_extra_rule(
                rule=rule,
                hits_count=hits_count,
                picks_count=picks_count,
                hit_by_bet_score_id=hit_by_bet_score_id,
            )
            if points <= 0:
                continue

            score_session.total_points += points
            self._session.add(
                ScoreSessionComponent(
                    score_session_id=score_session.id,
                    component_type=ScoreComponentType.EXTRA,
                    code=rule.code,
                    points=points,
                    details_json={
                        "scoring_rule_id": rule.id,
                        "evaluator_key": rule.evaluator_key,
                        "hits_count": hits_count,
                        "picks_count": picks_count,
                        "params": rule.params_json or {},
                    },
                )
            )
            count += 1

        return count
    
    def _apply_session_powerups(
        self,
        *,
        powerup_uses: list[PowerUpUse],
        powerup_restrictions: list[PowerUpRestriction],
        score_sessions_by_key: dict[tuple[int, int | None, int | None], ScoreSession],
    ) -> int:
        count = 0

        for powerup_use in powerup_uses:
            if (
                powerup_use.event_session_id is None
                and powerup_use.testing_event_session_id is None
            ):
                continue
            if not powerup_use.powerup.is_enabled:
                continue
            if self._is_powerup_restricted(
                powerup_use=powerup_use,
                restrictions=powerup_restrictions,
            ):
                continue

            base_points_by_user = {
                user_id: Decimal(str(score_session.base_points))
                for (
                    user_id,
                    event_session_id,
                    testing_event_session_id,
                ), score_session in score_sessions_by_key.items()
                if event_session_id == powerup_use.event_session_id
                and testing_event_session_id == powerup_use.testing_event_session_id
            }

            context = PowerUpEvaluationContext(
                powerup_code=powerup_use.powerup.code,
                actor_user_id=powerup_use.user_id,
                target_user_ids=self._resolve_powerup_target_user_ids(powerup_use),
                event_session_id=powerup_use.event_session_id,
                testing_event_session_id=powerup_use.testing_event_session_id,
                base_points_by_user=base_points_by_user,
                rule_json=powerup_use.rule_json or {},
            )

            evaluator = BasePowerUpEvaluator.get(powerup_use.powerup.code)

            for effect in evaluator.evaluate(context):
                key = (
                    effect.target_user_id,
                    powerup_use.event_session_id,
                    powerup_use.testing_event_session_id,
                )
                score_session = score_sessions_by_key.get(key)
                if score_session is None:
                    continue

                self._add_score_session_powerup_component(
                    score_session=score_session,
                    effect=effect,
                    component_code=f"{effect.code}_{powerup_use.id}",
                    powerup_use_id=powerup_use.id,
                )
                count += 1

        return count


    def _apply_extra_rules_to_score(
        self,
        *,
        score: Score,
        rules: list[ScoringRule],
        bet_context_id: int,
        event_session_id: int | None,
        hits_count: int,
        picks_count: int,
        hit_by_bet_score_id: dict[int, bool],
    ) -> int:
        count = 0

        for rule in self._matching_extra_rules(
            rules=rules,
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
        ):
            points = self._evaluate_extra_rule(
                rule=rule,
                hits_count=hits_count,
                picks_count=picks_count,
                hit_by_bet_score_id=hit_by_bet_score_id,
            )
            if points <= 0:
                continue

            score.total_points += points
            self._session.add(
                ScoreComponent(
                    score_id=score.id,
                    component_type=ScoreComponentType.EXTRA,
                    code=rule.code,
                    points=points,
                    details_json={
                        "scoring_rule_id": rule.id,
                        "evaluator_key": rule.evaluator_key,
                        "hits_count": hits_count,
                        "picks_count": picks_count,
                        "params": rule.params_json or {},
                    },
                )
            )
            count += 1

        return count
    

    def _matching_extra_rules(
        self,
        *,
        rules: list[ScoringRule],
        bet_context_id: int,
        event_session_id: int | None,
    ) -> list[ScoringRule]:
        matched: list[ScoringRule] = []

        for rule in rules:
            if rule.component_type != ScoreComponentType.EXTRA:
                continue

            if rule.scope == ScoringRuleScope.SESSION:
                if event_session_id is None:
                    continue
                if rule.bet_context_id == bet_context_id and rule.event_session_id == event_session_id:
                    matched.append(rule)

            elif rule.scope == ScoringRuleScope.CONTEXT:
                if rule.bet_context_id == bet_context_id:
                    matched.append(rule)

            elif rule.scope == ScoringRuleScope.GLOBAL:
                matched.append(rule)

        return matched
    
    def _evaluate_extra_rule(
        self,
        *,
        rule: ScoringRule,
        hits_count: int,
        picks_count: int,
        hit_by_bet_score_id: dict[int, bool],
    ) -> Decimal:
        params = rule.params_json or {}

        if rule.evaluator_key == "bonus_if_at_least_x_hits":
            min_hits = int(params.get("min_hits", 0))
            points = Decimal(str(params.get("points", 0)))
            return points if hits_count >= min_hits else Decimal("0")

        if rule.evaluator_key == "bonus_per_hit_from_x":
            min_hits = int(params.get("min_hits", 0))
            points_per_hit = Decimal(str(params.get("points_per_hit", 0)))
            include_threshold_hit = bool(params.get("include_threshold_hit", True))

            if hits_count < min_hits:
                return Decimal("0")

            bonus_hits = hits_count - min_hits
            if include_threshold_hit:
                bonus_hits += 1

            return Decimal(bonus_hits) * points_per_hit

        if rule.evaluator_key == "bonus_if_all_hits":
            points = Decimal(str(params.get("points", 0)))
            return points if picks_count > 0 and hits_count == picks_count else Decimal("0")

        if rule.evaluator_key == "bonus_if_all_bet_scores_hit":
            bet_score_ids = [int(value) for value in params.get("bet_score_ids", [])]
            points = Decimal(str(params.get("points", 0)))

            if not bet_score_ids:
                return Decimal("0")

            all_hit = all(
                hit_by_bet_score_id.get(bet_score_id) is True
                for bet_score_id in bet_score_ids
            )
            return points if all_hit else Decimal("0")

        return Decimal("0")

    
    def _add_score_powerup_component(
        self,
        *,
        score: Score,
        effect,
        component_code: str,
        powerup_use_id: int,
    ) -> None:
        points = Decimal(str(effect.points))
        component_type = ScoreComponentType(effect.component_type)

        if component_type == ScoreComponentType.POWERUP:
            score.total_points += points
        elif component_type == ScoreComponentType.PENALTY:
            points = min(points, Decimal(str(score.total_points)))
            score.total_points -= points

        self._session.add(
            ScoreComponent(
                score_id=score.id,
                component_type=component_type,
                code=component_code,
                points=points,
                details_json={
                    **effect.details,
                    "powerup_use_id": powerup_use_id,
                },
            )
        )

    def _add_score_session_powerup_component(
        self,
        *,
        score_session: ScoreSession,
        effect,
        component_code: str,
        powerup_use_id: int,
    ) -> None:
        points = Decimal(str(effect.points))
        component_type = ScoreComponentType(effect.component_type)

        if component_type == ScoreComponentType.POWERUP:
            score_session.total_points += points
        elif component_type == ScoreComponentType.PENALTY:
            points = min(points, Decimal(str(score_session.total_points)))
            score_session.total_points -= points

        self._session.add(
            ScoreSessionComponent(
                score_session_id=score_session.id,
                component_type=component_type,
                code=component_code,
                points=points,
                details_json={
                    **effect.details,
                    "powerup_use_id": powerup_use_id,
                },
            )
        )

    def _load_submitted_bets(self, scope: ScoringScope) -> list[Bet]:
        return self._session.scalars(
            select(Bet)
            .where(
                Bet.bet_context_id == scope.bet_context_id,
                Bet.submitted_at.is_not(None),
            )
            .options(joinedload(Bet.bet_picks).joinedload(BetPick.bet_score))
        ).unique().all()

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
    
    def _load_rules(self, scope: ScoringScope) -> list[ScoringRule]:
        return self._session.scalars(
            select(ScoringRule)
            .where(
                ScoringRule.season_id == scope.season_id,
                ScoringRule.is_enabled.is_(True),
            )
            .order_by(ScoringRule.priority.asc(), ScoringRule.id.asc())
        ).all()

    def _load_relations_by_source(self) -> dict[int, list[BetScoreRelation]]:
        rows = self._session.scalars(select(BetScoreRelation)).all()
        grouped: dict[int, list[BetScoreRelation]] = defaultdict(list)

        for row in rows:
            grouped[row.source_bet_score_id].append(row)

        return grouped
    
    def _load_powerup_uses(self, scope: ScoringScope) -> list[PowerUpUse]:
        return self._session.scalars(
            select(PowerUpUse)
            .where(PowerUpUse.bet_context_id == scope.bet_context_id)
            .options(
                joinedload(PowerUpUse.powerup),
                joinedload(PowerUpUse.targets),
            )
        ).unique().all()
    
    def _load_powerup_restrictions(self, scope: ScoringScope) -> list[PowerUpRestriction]:
        return self._session.scalars(
            select(PowerUpRestriction).where(
                PowerUpRestriction.bet_context_id == scope.bet_context_id,
                PowerUpRestriction.is_disabled.is_(True),
            )
        ).all()
    
    def _resolve_rule(
        self,
        *,
        rules: list[ScoringRule],
        component_type: ScoreComponentType,
        bet_context_id: int,
        bet_score_id: int | None,
        event_session_id: int | None,
    ) -> ScoringRule | None:
        scoped_rules = [rule for rule in rules if rule.component_type == component_type]

        for target_scope in (
            ScoringRuleScope.SESSION,
            ScoringRuleScope.CONTEXT,
            ScoringRuleScope.BET_SCORE,
            ScoringRuleScope.GLOBAL,
        ):
            for rule in scoped_rules:
                if rule.scope != target_scope:
                    continue

                if target_scope == ScoringRuleScope.SESSION:
                    if event_session_id is None:
                        continue
                    if (
                        rule.bet_context_id == bet_context_id
                        and rule.event_session_id == event_session_id
                    ):
                        return rule

                elif target_scope == ScoringRuleScope.CONTEXT:
                    if rule.bet_context_id == bet_context_id:
                        return rule

                elif target_scope == ScoringRuleScope.BET_SCORE:
                    if bet_score_id is not None and rule.bet_score_id == bet_score_id:
                        return rule

                elif target_scope == ScoringRuleScope.GLOBAL:
                    return rule

        return None
    
    def _is_powerup_restricted(
        self,
        *,
        powerup_use: PowerUpUse,
        restrictions: list[PowerUpRestriction],
    ) -> bool:
        for restriction in restrictions:
            if restriction.powerup_id != powerup_use.powerup_id:
                continue
            if restriction.bet_context_id != powerup_use.bet_context_id:
                continue
            if restriction.event_session_id != powerup_use.event_session_id:
                continue
            if restriction.testing_event_session_id != powerup_use.testing_event_session_id:
                continue
            return True

        return False
    
    def _resolve_powerup_target_user_ids(self, powerup_use: PowerUpUse) -> tuple[int, ...]:
        user_ids: set[int] = set()

        for target in powerup_use.targets:
            target_type = getattr(target.target_type, "value", target.target_type)

            if target_type == "USER" and target.target_user_id is not None:
                user_ids.add(target.target_user_id)

            elif target_type == "GROUP":
                user_ids.update(self._group_user_ids(target.target_group_id))

            elif target_type == "GROUP_EXCEPT_ACTOR":
                user_ids.update(
                    user_id
                    for user_id in self._group_user_ids(target.target_group_id)
                    if user_id != powerup_use.user_id
                )

            elif target_type == "ALL":
                user_ids.update(self._group_user_ids(powerup_use.group_id))

        return tuple(user_ids)

    def _group_user_ids(self, group_id: int | None) -> tuple[int, ...]:
        if group_id is None:
            return ()

        return tuple(
            self._session.scalars(
                select(GroupMembership.user_id).where(
                    GroupMembership.group_id == group_id
                )
            ).all()
        )