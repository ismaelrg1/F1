from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.betting import BetContext
from app.db.competition import EventSession, RaceEvent, Season, TestingEvent, TestingEventSession
from app.db.enums import BetContextKind
from app.db.scoring import OfficialResult, ResultPublication, Score, ScoreSession
from app.domain.management.result_publications.models import ResultPublicationResult


class SqlAlchemyResultPublicationRepository:
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
