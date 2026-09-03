from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.db.betting import Bet, BetContext, BetPick, BetScoreRelation, BetTemplate, BetTemplateItem
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
    ScoringBetScoreConfig,
    PowerUpEvaluationContext,
)
from app.domain.management.scoring.extra_evaluators import (
    BaseExtraEvaluator,
    ExtraEvaluationDataset,
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
        effective_configs = self._load_effective_bet_score_configs(scope)
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
                    effective_configs=effective_configs,
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
                    effective_configs=effective_configs,
                )
                scores_by_user[bet.user_id] = score
                score_components_count += count

        self._session.flush()

        extra_score_count, extra_session_count = self._apply_extra_rules(
            scope=scope,
            rules=rules,
            bets=bets,
            scores_by_user=scores_by_user,
            score_sessions_by_key=score_sessions_by_key,
        )
        score_components_count += extra_score_count
        score_session_components_count += extra_session_count

        score_components_count += self._apply_context_powerups(
            scope=scope,
            powerup_uses=powerup_uses,
            powerup_restrictions=powerup_restrictions,
            scores_by_user=scores_by_user,
            score_sessions_by_key=score_sessions_by_key,
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

    def _load_effective_bet_score_configs(
        self,
        scope: ScoringScope,
    ) -> dict[tuple[int, str | None], ScoringBetScoreConfig]:
        context = self._session.get(BetContext, scope.bet_context_id)
        if context is None:
            return {}

        templates = self._session.scalars(
            select(BetTemplate)
            .where(
                BetTemplate.season_id == scope.season_id,
                BetTemplate.context_kind == context.kind,
            )
            .options(joinedload(BetTemplate.items).joinedload(BetTemplateItem.bet_score))
        ).unique().all()

        configs: dict[tuple[int, str | None], ScoringBetScoreConfig] = {}

        for template in templates:
            session_type = (
                getattr(template.session_type, "value", template.session_type)
                if template.session_type is not None
                else None
            )

            for item in template.items:
                bet_score = item.bet_score

                points = (
                    Decimal(str(item.override_points))
                    if item.override_points is not None
                    else Decimal(str(bet_score.base_points))
                )

                constraints_json = (
                    item.override_constraints_json
                    if item.override_constraints_json is not None
                    else bet_score.constraints_json
                )

                configs[(bet_score.id, session_type)] = ScoringBetScoreConfig(
                    points=points,
                    constraints_json=constraints_json,
                )

        return configs

    def _apply_extra_rules(
        self,
        *,
        scope: ScoringScope,
        rules: list[ScoringRule],
        bets: list[Bet],
        scores_by_user: dict[int, Score],
        score_sessions_by_key: dict[tuple[int, int | None, int | None], ScoreSession],
    ) -> tuple[int, int]:
        extra_rules = [
            rule
            for rule in rules
            if rule.component_type == ScoreComponentType.EXTRA
            and BaseExtraEvaluator.supports(rule.evaluator_key)
            and (
                rule.scope == ScoringRuleScope.GLOBAL
                or (
                    rule.scope == ScoringRuleScope.CONTEXT
                    and rule.bet_context_id == scope.bet_context_id
                )
            )
        ]

        score_components_count = 0
        score_session_components_count = 0

        self._session.flush()

        for rule in extra_rules:
            evaluator = BaseExtraEvaluator.get(rule.evaluator_key)
            effects = evaluator.evaluate_many(
                ExtraEvaluationDataset(
                    scope=scope,
                    rule=rule,
                    bets=bets,
                    scores_by_user=scores_by_user,
                    score_sessions_by_key=score_sessions_by_key,
                )
            )

            for effect in effects:
                if effect.points <= 0:
                    continue

                if effect.event_session_id is not None or effect.testing_event_session_id is not None:
                    score_session = score_sessions_by_key.get(
                        (effect.user_id, effect.event_session_id, effect.testing_event_session_id)
                    )
                    if score_session is None:
                        continue

                    score_session.total_points += effect.points
                    self._session.add(
                        ScoreSessionComponent(
                            score_session_id=score_session.id,
                            component_type=ScoreComponentType.EXTRA,
                            code=effect.code,
                            points=effect.points,
                            details_json=effect.details,
                        )
                    )
                    score_session_components_count += 1
                    continue

                score = scores_by_user.get(effect.user_id)
                if score is None:
                    score = Score(
                        user_id=effect.user_id,
                        bet_context_id=scope.bet_context_id,
                        base_points=Decimal("0"),
                        total_points=Decimal("0"),
                    )
                    self._session.add(score)
                    self._session.flush()
                    scores_by_user[effect.user_id] = score

                score.total_points += effect.points
                self._session.add(
                    ScoreComponent(
                        score_id=score.id,
                        component_type=ScoreComponentType.EXTRA,
                        code=effect.code,
                        points=effect.points,
                        details_json=effect.details,
                    )
                )
                score_components_count += 1

        return score_components_count, score_session_components_count

    def _calculate_context_bet(
        self,
        *,
        bet: Bet,
        picks: list[BetPick],
        official_results: dict,
        rules: list[ScoringRule],
        relations_by_source: dict[int, list[BetScoreRelation]],
        effective_configs: dict[tuple[int, str | None], ScoringBetScoreConfig],
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
                effective_configs=effective_configs,
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
                        "hit": evaluation.hit,
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

        return score, components_count

    def _calculate_session_bet(
        self,
        *,
        bet: Bet,
        picks: list[BetPick],
        official_results: dict,
        rules: list[ScoringRule],
        relations_by_source: dict[int, list[BetScoreRelation]],
        effective_configs: dict[tuple[int, str | None], ScoringBetScoreConfig],
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
                effective_configs=effective_configs,
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
                        "hit": evaluation.hit,
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
        effective_configs: dict[tuple[int, str | None], ScoringBetScoreConfig],
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
        effective_config = self._resolve_effective_config(
            bet=bet,
            pick=pick,
            effective_configs=effective_configs,
        )

        evaluation = evaluator.evaluate(
            pick=pick,
            official_result=official_result,
            bet_score=pick.bet_score,
            rule=rule,
            effective_config=effective_config,
            relations=relations_by_source.get(pick.bet_score_id, []),
            related_picks=picks_by_score_id,
        )

        return evaluation, official_result, rule

    def _resolve_effective_config(
        self,
        *,
        bet: Bet,
        pick: BetPick,
        effective_configs: dict[tuple[int, str | None], ScoringBetScoreConfig],
    ) -> ScoringBetScoreConfig | None:
        session_type = None

        if bet.event_session_id is not None:
            event_session = self._session.get(EventSession, bet.event_session_id)
            if event_session is not None:
                session_type = getattr(
                    event_session.session_type,
                    "value",
                    event_session.session_type,
                )

        return (
            effective_configs.get((pick.bet_score_id, session_type))
            or effective_configs.get((pick.bet_score_id, None))
        )

    def _apply_context_powerups(
        self,
        *,
        scope: ScoringScope,
        powerup_uses: list[PowerUpUse],
        powerup_restrictions: list[PowerUpRestriction],
        scores_by_user: dict[int, Score],
        score_sessions_by_key: dict[tuple[int, int | None, int | None], ScoreSession],
    ) -> int:
        count = 0
        points_by_user = self._context_powerup_base_points_by_user(
            scope=scope,
            powerup_use=None,
            scores_by_user=scores_by_user,
            score_sessions_by_key=score_sessions_by_key,
        )

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
            apply_to = self._context_powerup_apply_to(powerup_use)
            if apply_to == {"context": True, "session_types": None}:
                applicable_points_by_user = dict(points_by_user)
            else:
                applicable_points_by_user = self._context_powerup_base_points_by_user(
                    scope=scope,
                    powerup_use=powerup_use,
                    scores_by_user=scores_by_user,
                    score_sessions_by_key=score_sessions_by_key,
                )

            context = PowerUpEvaluationContext(
                powerup_code=powerup_use.powerup.code,
                actor_user_id=powerup_use.user_id,
                target_user_ids=self._resolve_powerup_target_user_ids(powerup_use),
                event_session_id=None,
                testing_event_session_id=None,
                base_points_by_user=applicable_points_by_user,
                rule_json=powerup_use.rule_json or {},
            )

            evaluator = BasePowerUpEvaluator.get(powerup_use.powerup.code)

            for effect in evaluator.evaluate(context):
                score = scores_by_user.get(effect.target_user_id)
                if score is None:
                    score = Score(
                        user_id=effect.target_user_id,
                        bet_context_id=scope.bet_context_id,
                        base_points=Decimal("0"),
                        total_points=Decimal("0"),
                    )
                    self._session.add(score)
                    self._session.flush()
                    scores_by_user[effect.target_user_id] = score

                component_count = self._add_context_powerup_components(
                    score=score,
                    effect=effect,
                    component_code=f"{effect.code}_{powerup_use.id}",
                    powerup_use_id=powerup_use.id,
                    powerup_use=powerup_use,
                    score_sessions_by_key=score_sessions_by_key,
                )
                effect_points = Decimal(str(effect.points))
                current_points = points_by_user.get(effect.target_user_id, Decimal("0"))
                if ScoreComponentType(effect.component_type) == ScoreComponentType.POWERUP:
                    points_by_user[effect.target_user_id] = current_points + effect_points
                elif ScoreComponentType(effect.component_type) == ScoreComponentType.PENALTY:
                    points_by_user[effect.target_user_id] = (
                        current_points - min(effect_points, current_points)
                    )
                count += component_count

        return count

    def _context_powerup_base_points_by_user(
        self,
        *,
        scope: ScoringScope,
        powerup_use: PowerUpUse | None,
        scores_by_user: dict[int, Score],
        score_sessions_by_key: dict[tuple[int, int | None, int | None], ScoreSession],
    ) -> dict[int, Decimal]:
        apply_to = (
            self._context_powerup_apply_to(powerup_use)
            if powerup_use is not None
            else {"context": True, "session_types": None}
        )
        include_context = apply_to["context"]
        session_types = apply_to["session_types"]

        base_points_by_user: dict[int, Decimal] = {}
        if include_context:
            base_points_by_user.update(
                {
                    user_id: Decimal(str(score.base_points))
                    for user_id, score in scores_by_user.items()
                }
            )

        if scope.is_race_event:
            for (
                user_id,
                event_session_id,
                testing_event_session_id,
            ), score_session in score_sessions_by_key.items():
                if event_session_id is None or testing_event_session_id is not None:
                    continue
                if isinstance(session_types, set):
                    if not session_types:
                        continue
                    if score_session.event_session is None:
                        continue
                    session_type = getattr(
                        score_session.event_session.session_type,
                        "value",
                        score_session.event_session.session_type,
                    )
                    session_type = self._normalize_apply_to_session_type(session_type)
                    if session_type not in session_types:
                        continue

                base_points_by_user[user_id] = (
                    base_points_by_user.get(user_id, Decimal("0"))
                    + Decimal(str(score_session.base_points))
                )

        return base_points_by_user

    def _context_powerup_apply_to(self, powerup_use: PowerUpUse) -> dict:
        rule_json = powerup_use.rule_json or {}
        apply_to = rule_json.get("apply_to")
        if not isinstance(apply_to, dict):
            return {"context": True, "session_types": None}

        context = bool(apply_to.get("context", False))
        raw_session_types = apply_to.get("session_types")

        if raw_session_types is None:
            session_types = None
        elif isinstance(raw_session_types, list):
            session_types = {
                self._normalize_apply_to_session_type(session_type)
                for session_type in raw_session_types
            }
        else:
            session_types = set()

        return {"context": context, "session_types": session_types}

    def _normalize_apply_to_session_type(self, session_type: object) -> str:
        return str(session_type).strip().upper().replace(" ", "_").replace("-", "_")

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

    def _add_context_powerup_components(
        self,
        *,
        score: Score,
        effect,
        component_code: str,
        powerup_use_id: int,
        powerup_use: PowerUpUse,
        score_sessions_by_key: dict[tuple[int, int | None, int | None], ScoreSession],
    ) -> int:
        component_type = ScoreComponentType(effect.component_type)
        if component_type != ScoreComponentType.PENALTY:
            self._add_score_powerup_component(
                score=score,
                effect=effect,
                component_code=component_code,
                powerup_use_id=powerup_use_id,
            )
            return 1

        remaining_points = Decimal(str(effect.points))
        component_count = 0
        context_points = min(remaining_points, Decimal(str(score.total_points)))

        if context_points > 0:
            context_effect = replace(effect, points=context_points)
            self._add_score_powerup_component(
                score=score,
                effect=context_effect,
                component_code=component_code,
                powerup_use_id=powerup_use_id,
            )
            remaining_points -= context_points
            component_count += 1

        if remaining_points <= 0:
            return component_count

        for score_session in self._context_powerup_score_sessions(
            powerup_use=powerup_use,
            target_user_id=effect.target_user_id,
            score_sessions_by_key=score_sessions_by_key,
        ):
            session_points = min(remaining_points, Decimal(str(score_session.total_points)))
            if session_points <= 0:
                continue

            session_effect = replace(effect, points=session_points)
            self._add_score_session_powerup_component(
                score_session=score_session,
                effect=session_effect,
                component_code=f"{component_code}_{score_session.id}",
                powerup_use_id=powerup_use_id,
            )
            remaining_points -= session_points
            component_count += 1

            if remaining_points <= 0:
                break

        return component_count

    def _context_powerup_score_sessions(
        self,
        *,
        powerup_use: PowerUpUse,
        target_user_id: int,
        score_sessions_by_key: dict[tuple[int, int | None, int | None], ScoreSession],
    ) -> list[ScoreSession]:
        apply_to = self._context_powerup_apply_to(powerup_use)
        session_types = apply_to["session_types"]
        sessions: list[ScoreSession] = []

        if isinstance(session_types, set) and not session_types:
            return sessions

        for (
            user_id,
            event_session_id,
            testing_event_session_id,
        ), score_session in score_sessions_by_key.items():
            if user_id != target_user_id:
                continue
            if event_session_id is None or testing_event_session_id is not None:
                continue
            if isinstance(session_types, set):
                if score_session.event_session is None:
                    continue
                session_type = getattr(
                    score_session.event_session.session_type,
                    "value",
                    score_session.event_session.session_type,
                )
                if self._normalize_apply_to_session_type(session_type) not in session_types:
                    continue
            sessions.append(score_session)

        return sessions

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
            .order_by(PowerUpUse.used_at.asc(), PowerUpUse.id.asc())
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
