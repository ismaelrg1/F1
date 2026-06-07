from uuid import UUID
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.db.betting import BetContext
from app.db.competition import EventSession, RaceEvent, Season, TestingEvent, TestingEventSession
from app.db.enums import BetContextKind, RankingEventType, ScoreComponentType
from app.db.scoring import(
    OfficialResult,
    ResultPublication,
    Score,
    ScoreComponent,
    ScoreSeasonAggregate,
    ScoreSession,
    ScoreSessionComponent,
)
from app.domain.management.result_publications.models import ResultPublicationResult

from app.domain.management.result_publications.ports import ResultPublicationRepository


class SqlAlchemyResultPublicationRepository(ResultPublicationRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_race_bet_context_id(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
    ) -> int | None:
        stmt = (
            select(BetContext.id)
            .join(RaceEvent, RaceEvent.id == BetContext.race_event_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.GP,
                RaceEvent.public_id == race_event_public_id,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_testing_bet_context_id(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
    ) -> int | None:
        stmt = (
            select(BetContext.id)
            .join(TestingEvent, TestingEvent.id == BetContext.testing_event_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.PRETESTING,
                TestingEvent.public_id == testing_event_public_id,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_season_bet_context_id(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> int | None:
        stmt = (
            select(BetContext.id)
            .join(Season, Season.id == BetContext.season_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.SEASON,
                BetContext.race_event_id.is_(None),
                BetContext.testing_event_id.is_(None),
                Season.year == season_year,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_event_session_id(
        self,
        *,
        bet_context_id: int,
        event_session_public_id: UUID,
    ) -> int | None:
        stmt = (
            select(EventSession.id)
            .join(BetContext, BetContext.race_event_id == EventSession.race_event_id)
            .where(
                BetContext.id == bet_context_id,
                EventSession.public_id == event_session_public_id,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_testing_event_session_id(
        self,
        *,
        bet_context_id: int,
        testing_event_session_public_id: UUID,
    ) -> int | None:
        stmt = (
            select(TestingEventSession.id)
            .join(BetContext, BetContext.testing_event_id == TestingEventSession.testing_event_id)
            .where(
                BetContext.id == bet_context_id,
                TestingEventSession.public_id == testing_event_session_public_id,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def official_results_exist(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        stmt = self._official_result_scope_stmt(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
        )
        return self._session.execute(stmt).first() is not None

    def publication_exists(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        stmt = self._publication_scope_stmt(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
        )
        return self._session.execute(stmt).first() is not None


    def has_calculated_scores(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> bool:
        if event_session_id is not None:
            stmt = select(ScoreSession.id).where(
                ScoreSession.bet_context_id == bet_context_id,
                ScoreSession.event_session_id == event_session_id,
                ScoreSession.testing_event_session_id.is_(None),
            )
            return self._session.execute(stmt).first() is not None

        if testing_event_session_id is not None:
            stmt = select(ScoreSession.id).where(
                ScoreSession.bet_context_id == bet_context_id,
                ScoreSession.testing_event_session_id == testing_event_session_id,
                ScoreSession.event_session_id.is_(None),
            )
            return self._session.execute(stmt).first() is not None

        stmt = select(Score.id).where(
            Score.bet_context_id == bet_context_id,
        )
        return self._session.execute(stmt).first() is not None
    
    def recalculate_season_aggregates_for_bet_context(
        self,
        *,
        bet_context_id: int,
    ) -> None:
        context = self._session.execute(
            select(BetContext).where(BetContext.id == bet_context_id)
        ).scalar_one()

        group_id = context.group_id
        season_id = context.season_id

        previous_positions = {
            row.user_id: row.position
            for row in self._session.scalars(
                select(ScoreSeasonAggregate).where(
                    ScoreSeasonAggregate.group_id == group_id,
                    ScoreSeasonAggregate.season_id == season_id,
                )
            ).all()
        }

        self._session.execute(
            delete(ScoreSeasonAggregate).where(
                ScoreSeasonAggregate.group_id == group_id,
                ScoreSeasonAggregate.season_id == season_id,
            )
        )

        totals: dict[int, dict] = defaultdict(self._empty_aggregate_totals)

        publications = self._session.scalars(
            select(ResultPublication)
            .join(BetContext, BetContext.id == ResultPublication.bet_context_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.season_id == season_id,
            )
            .options(
                joinedload(ResultPublication.bet_context).joinedload(BetContext.race_event),
                joinedload(ResultPublication.bet_context).joinedload(BetContext.testing_event),
                joinedload(ResultPublication.bet_context).joinedload(BetContext.season),
                joinedload(ResultPublication.event_session),
                joinedload(ResultPublication.testing_event_session),
            )
        ).all()

        last_event = self._resolve_last_published_event(publications)

        for publication in publications:
            published_context = publication.bet_context

            if publication.event_session_id is not None:
                self._add_published_score_sessions_to_aggregate(
                    totals=totals,
                    bet_context_id=publication.bet_context_id,
                    event_session_id=publication.event_session_id,
                    testing_event_session_id=None,
                    points_bucket="race_points",
                )
                continue

            if publication.testing_event_session_id is not None:
                self._add_published_score_sessions_to_aggregate(
                    totals=totals,
                    bet_context_id=publication.bet_context_id,
                    event_session_id=None,
                    testing_event_session_id=publication.testing_event_session_id,
                    points_bucket="testing_points",
                )
                continue

            if published_context.kind == BetContextKind.SEASON:
                points_bucket = "season_points"
            elif published_context.kind == BetContextKind.PRETESTING:
                points_bucket = "testing_points"
            else:
                points_bucket = "race_points"

            self._add_published_scores_to_aggregate(
                totals=totals,
                bet_context_id=publication.bet_context_id,
                points_bucket=points_bucket,
            )

        ranked = sorted(
            totals.items(),
            key=lambda item: (-item[1]["total_points"], item[0]),
        )

        now = datetime.now(timezone.utc)

        for position, (user_id, values) in enumerate(ranked, start=1):
            self._session.add(
                ScoreSeasonAggregate(
                    group_id=group_id,
                    season_id=season_id,
                    user_id=user_id,
                    total_points=values["total_points"],
                    race_points=values["race_points"],
                    testing_points=values["testing_points"],
                    season_points=values["season_points"],
                    extra_points=values["extra_points"],
                    penalty_points=values["penalty_points"],
                    position=position,
                    previous_position=previous_positions.get(user_id),
                    last_event_type=last_event["type"],
                    last_event_label=last_event["label"],
                    last_event_order=last_event["order"],
                    last_scored_at=now,
                )
            )

        self._session.flush()


    def create_publication(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        published_by_user_id: int,
        note: str | None,
    ) -> ResultPublicationResult:
        row = ResultPublication(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
            published_by_user_id=published_by_user_id,
            note=note,
        )
        self._session.add(row)
        self._session.flush()

        return self._reload_publication(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
        )

    def delete_publication(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> None:
        publication = self._session.execute(
            self._publication_scope_stmt(
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
            )
        ).scalar_one()

        self._session.delete(publication)
        self._session.flush()

    def _empty_aggregate_totals(self) -> dict:
        return {
            "total_points": Decimal("0"),
            "race_points": Decimal("0"),
            "testing_points": Decimal("0"),
            "season_points": Decimal("0"),
            "extra_points": Decimal("0"),
            "penalty_points": Decimal("0"),
        }
    
    def _add_published_scores_to_aggregate(
        self,
        *,
        totals: dict[int, dict],
        bet_context_id: int,
        points_bucket: str,
    ) -> None:
        scores = self._session.scalars(
            select(Score).where(Score.bet_context_id == bet_context_id)
        ).all()

        for score in scores:
            values = totals[score.user_id]
            points = Decimal(str(score.total_points))

            values["total_points"] += points
            values[points_bucket] += points

            self._add_score_component_totals(
                values=values,
                score_id=score.id,
            )

    def _add_published_score_sessions_to_aggregate(
        self,
        *,
        totals: dict[int, dict],
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        points_bucket: str,
    ) -> None:
        stmt = select(ScoreSession).where(
            ScoreSession.bet_context_id == bet_context_id,
        )

        if event_session_id is None:
            stmt = stmt.where(ScoreSession.event_session_id.is_(None))
        else:
            stmt = stmt.where(ScoreSession.event_session_id == event_session_id)

        if testing_event_session_id is None:
            stmt = stmt.where(ScoreSession.testing_event_session_id.is_(None))
        else:
            stmt = stmt.where(ScoreSession.testing_event_session_id == testing_event_session_id)

        score_sessions = self._session.scalars(stmt).all()

        for score_session in score_sessions:
            values = totals[score_session.user_id]
            points = Decimal(str(score_session.total_points))

            values["total_points"] += points
            values[points_bucket] += points

            self._add_score_session_component_totals(
                values=values,
                score_session_id=score_session.id,
            )

    def _add_score_component_totals(
        self,
        *,
        values: dict,
        score_id: int,
    ) -> None:
        components = self._session.scalars(
            select(ScoreComponent).where(ScoreComponent.score_id == score_id)
        ).all()

        for component in components:
            points = Decimal(str(component.points))

            if component.component_type == ScoreComponentType.EXTRA:
                values["extra_points"] += points
            elif component.component_type == ScoreComponentType.PENALTY:
                values["penalty_points"] += points
    

    def _add_score_session_component_totals(
        self,
        *,
        values: dict,
        score_session_id: int,
    ) -> None:
        components = self._session.scalars(
            select(ScoreSessionComponent).where(
                ScoreSessionComponent.score_session_id == score_session_id
            )
        ).all()

        for component in components:
            points = Decimal(str(component.points))

            if component.component_type == ScoreComponentType.EXTRA:
                values["extra_points"] += points
            elif component.component_type == ScoreComponentType.PENALTY:
                values["penalty_points"] += points

    def _resolve_last_published_event(self, publications: list[ResultPublication]) -> dict:
        if not publications:
            return {
                "type": None,
                "label": None,
                "order": None,
            }

        publication = max(
            publications,
            key=self._publication_calendar_order_key,
        )
        context = publication.bet_context

        if context.kind == BetContextKind.SEASON:
            return {
                "type": RankingEventType.SEASON,
                "label": context.label,
                "order": None,
            }

        if context.kind == BetContextKind.PRETESTING:
            return {
                "type": RankingEventType.TESTING_EVENT,
                "label": context.label,
                "order": self._testing_publication_order(publication),
            }

        return {
            "type": RankingEventType.RACE_EVENT,
            "label": context.label,
            "order": self._race_publication_order(publication),
        }
    
    def _publication_calendar_order_key(self, publication: ResultPublication) -> tuple:
        context = publication.bet_context

        if context.kind == BetContextKind.SEASON:
            return (
                3,
                context.season.year if context.season is not None else 0,
                0,
                0,
            )

        if context.kind == BetContextKind.PRETESTING:
            return (
                1,
                context.season.year if context.season is not None else 0,
                self._testing_publication_order(publication) or 0,
                0,
            )

        return (
            2,
            context.season.year if context.season is not None else 0,
            self._race_publication_order(publication) or 0,
            self._race_session_publication_order(publication) or 0,
        )
    
    def _race_publication_order(self, publication: ResultPublication) -> int | None:
        race_event = publication.bet_context.race_event
        if race_event is None:
            return None

        return race_event.round_number
    
    def _race_session_publication_order(self, publication: ResultPublication) -> int | None:
        if publication.event_session is None:
            return None

        order_by_session_type = {
            "FP1": 1,
            "FP2": 2,
            "FP3": 3,
            "SPRINT_QUALY": 4,
            "SPRINT": 5,
            "QUALY": 6,
            "RACE": 7,
        }

        session_type = getattr(publication.event_session.session_type, "value", publication.event_session.session_type)
        return order_by_session_type.get(session_type, 0)
    

    def _testing_publication_order(self, publication: ResultPublication) -> int | None:
        testing_event = publication.bet_context.testing_event
        testing_session = publication.testing_event_session

        if testing_session is not None:
            return testing_session.session_order

        if testing_event is not None:
            return 0

        return None

    def _reload_publication(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ) -> ResultPublicationResult:
        row = self._session.execute(
            self._publication_scope_stmt(
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
            )
        ).scalar_one()

        return self._map_publication(row)

    def _official_result_scope_stmt(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ):
        stmt = select(OfficialResult).where(OfficialResult.bet_context_id == bet_context_id)

        if event_session_id is None:
            stmt = stmt.where(OfficialResult.event_session_id.is_(None))
        else:
            stmt = stmt.where(OfficialResult.event_session_id == event_session_id)

        if testing_event_session_id is None:
            stmt = stmt.where(OfficialResult.testing_event_session_id.is_(None))
        else:
            stmt = stmt.where(OfficialResult.testing_event_session_id == testing_event_session_id)

        return stmt

    def _publication_scope_stmt(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ):
        stmt = (
            select(ResultPublication)
            .where(ResultPublication.bet_context_id == bet_context_id)
            .options(
                joinedload(ResultPublication.bet_context).joinedload(BetContext.race_event),
                joinedload(ResultPublication.bet_context).joinedload(BetContext.testing_event),
                joinedload(ResultPublication.bet_context).joinedload(BetContext.season),
                joinedload(ResultPublication.event_session),
                joinedload(ResultPublication.testing_event_session),
            )
        )

        if event_session_id is None:
            stmt = stmt.where(ResultPublication.event_session_id.is_(None))
        else:
            stmt = stmt.where(ResultPublication.event_session_id == event_session_id)

        if testing_event_session_id is None:
            stmt = stmt.where(ResultPublication.testing_event_session_id.is_(None))
        else:
            stmt = stmt.where(ResultPublication.testing_event_session_id == testing_event_session_id)

        return stmt

    def _map_publication(self, row: ResultPublication) -> ResultPublicationResult:
        context = row.bet_context

        return ResultPublicationResult(
            race_event_public_id=context.race_event.public_id if context.race_event is not None else None,
            event_session_public_id=row.event_session.public_id if row.event_session is not None else None,
            testing_event_public_id=context.testing_event.public_id if context.testing_event is not None else None,
            testing_event_session_public_id=(
                row.testing_event_session.public_id
                if row.testing_event_session is not None
                else None
            ),
            season_year=context.season.year if context.season is not None else None,
            published_at=row.published_at,
            note=row.note,
        )
