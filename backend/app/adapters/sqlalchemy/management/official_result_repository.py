from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.social import GroupMembership
from app.db.betting import BetContext, BetScore
from app.db.competition import EventSession, TestingEventSession
from app.db.scoring import OfficialResult as OfficialResultORM
from app.db.scoring import ResultPublication
from app.db.scoring.official_result import SourceType
from app.domain.management.official_results.answers.models import OfficialResultInput
from app.domain.management.official_results.questions.models import ExistingOfficialResult, OfficialResultScopeKey
from app.domain.management.official_results.models import OfficialResult as OfficialResultDomain

from app.db.competition import RaceEvent, Season, TestingEvent
from app.db.enums import BetContextKind

from app.domain.management.official_results.ports import OfficialResultRepository


class SqlAlchemyOfficialResultRepository(OfficialResultRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_bet_context_scope(
        self,
        *,
        bet_context_public_id: UUID,
    ) -> tuple[int, UUID]:
        bet_context = self._session.execute(
            select(BetContext).where(BetContext.public_id == bet_context_public_id)
        ).scalar_one_or_none()

        if bet_context is None:
            raise ValueError("bet_context_not_found")

        return bet_context.id, bet_context.public_id

    def get_event_session_scope(
        self,
        *,
        bet_context_id: int,
        event_session_public_id: UUID,
    ) -> tuple[int, UUID] | None:
        stmt = (
            select(EventSession)
            .join(BetContext, BetContext.race_event_id == EventSession.race_event_id)
            .where(
                BetContext.id == bet_context_id,
                EventSession.public_id == event_session_public_id,
            )
        )

        session = self._session.execute(stmt).scalar_one_or_none()
        if session is None:
            return None

        return session.id, session.public_id

    def get_testing_event_session_scope(
        self,
        *,
        bet_context_id: int,
        testing_event_session_public_id: UUID,
    ) -> tuple[int, UUID] | None:
        stmt = (
            select(TestingEventSession)
            .join(BetContext, BetContext.testing_event_id == TestingEventSession.testing_event_id)
            .where(
                BetContext.id == bet_context_id,
                TestingEventSession.public_id == testing_event_session_public_id,
            )
        )

        session = self._session.execute(stmt).scalar_one_or_none()
        if session is None:
            return None

        return session.id, session.public_id

    def get_bet_score_ids_by_codes(
        self,
        *,
        codes: set[str],
    ) -> dict[str, int]:
        if not codes:
            return {}

        rows = self._session.execute(
            select(BetScore.code, BetScore.id).where(BetScore.code.in_(codes))
        ).all()

        return {code: score_id for code, score_id in rows}

    def official_results_exist_for_scope(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        bet_score_ids: set[int],
    ) -> bool:
        if not bet_score_ids:
            return False

        stmt = self._scope_stmt(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
        ).where(OfficialResultORM.bet_score_id.in_(bet_score_ids))

        return self._session.execute(stmt).first() is not None

    def official_results_missing_for_scope(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        bet_score_ids: set[int],
    ) -> bool:
        stmt = self._scope_stmt(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
        ).where(OfficialResultORM.bet_score_id.in_(bet_score_ids))

        existing_ids = {
            item.bet_score_id
            for item in self._session.execute(stmt).scalars().all()
        }

        return existing_ids != bet_score_ids

    def create_official_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        source: SourceType,
        results: list[OfficialResultInput],
        score_ids_by_code: dict[str, int],
    ) -> list[OfficialResultDomain]:
        rows: list[OfficialResultORM] = []

        for item in results:
            row = OfficialResultORM(
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
                bet_score_id=score_ids_by_code[item.bet_score_code],
                value=item.value,
                source=source,
            )
            self._session.add(row)
            rows.append(row)

        self._session.flush()

        return self._reload_results(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
            bet_score_ids={score_ids_by_code[item.bet_score_code] for item in results},
        )

    def update_official_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        source: SourceType,
        results: list[OfficialResultInput],
        score_ids_by_code: dict[str, int],
    ) -> list[OfficialResultDomain]:
        stmt = self._scope_stmt(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
        ).options(joinedload(OfficialResultORM.bet_score))

        existing = {
            row.bet_score_id: row
            for row in self._session.execute(stmt).scalars().all()
        }

        for item in results:
            score_id = score_ids_by_code[item.bet_score_code]
            row = existing[score_id]
            row.value = item.value
            row.source = source

        self._session.flush()

        return self._reload_results(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
            bet_score_ids={score_ids_by_code[item.bet_score_code] for item in results},
        )
    
    def get_bet_context_group_id(
        self,
        *,
        bet_context_public_id: UUID,
    ) -> int | None:
        stmt = select(BetContext.group_id).where(
            BetContext.public_id == bet_context_public_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()


    def get_group_role(
        self,
        *,
        user_id: int,
        group_id: int,
    ) -> str | None:
        stmt = select(GroupMembership.role).where(
            GroupMembership.user_id == user_id,
            GroupMembership.group_id == group_id,
        )
        role = self._session.execute(stmt).scalar_one_or_none()
        return None if role is None else role.value
    
    def get_race_bet_context_public_id(
        self,
        *,
        group_id: int,
        race_event_public_id: UUID,
    ) -> UUID | None:
        stmt = (
            select(BetContext.public_id)
            .join(RaceEvent, RaceEvent.id == BetContext.race_event_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.GP,
                RaceEvent.public_id == race_event_public_id,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_testing_bet_context_public_id(
        self,
        *,
        group_id: int,
        testing_event_public_id: UUID,
    ) -> UUID | None:
        stmt = (
            select(BetContext.public_id)
            .join(TestingEvent, TestingEvent.id == BetContext.testing_event_id)
            .where(
                BetContext.group_id == group_id,
                BetContext.kind == BetContextKind.PRETESTING,
                TestingEvent.public_id == testing_event_public_id,
            )
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_season_bet_context_public_id(
        self,
        *,
        group_id: int,
        season_year: int,
    ) -> UUID | None:
        stmt = (
            select(BetContext.public_id)
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
    
    def list_official_results_for_context(
        self,
        *,
        bet_context_id: int,
    ) -> list[ExistingOfficialResult]:
        stmt = (
            select(OfficialResultORM)
            .where(OfficialResultORM.bet_context_id == bet_context_id)
            .options(
                joinedload(OfficialResultORM.event_session),
                joinedload(OfficialResultORM.testing_event_session),
                joinedload(OfficialResultORM.bet_score),
            )
        )

        rows = self._session.execute(stmt).scalars().all()

        return [
            ExistingOfficialResult(
                event_session_public_id=(
                    row.event_session.public_id
                    if row.event_session is not None
                    else None
                ),
                testing_event_session_public_id=(
                    row.testing_event_session.public_id
                    if row.testing_event_session is not None
                    else None
                ),
                bet_score_code=row.bet_score.code,
                value=row.value,
                source=row.source,
                created_at=row.created_at,
            )
            for row in rows
        ]


    def list_result_publications_for_context(
        self,
        *,
        bet_context_id: int,
    ) -> set[OfficialResultScopeKey]:
        stmt = (
            select(ResultPublication)
            .where(ResultPublication.bet_context_id == bet_context_id)
            .options(
                joinedload(ResultPublication.event_session),
                joinedload(ResultPublication.testing_event_session),
            )
        )

        rows = self._session.execute(stmt).scalars().all()

        return {
            OfficialResultScopeKey(
                event_session_public_id=(
                    row.event_session.public_id
                    if row.event_session is not None
                    else None
                ),
                testing_event_session_public_id=(
                    row.testing_event_session.public_id
                    if row.testing_event_session is not None
                    else None
                ),
            )
            for row in rows
        }

    def _reload_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        bet_score_ids: set[int],
    ) -> list[OfficialResultDomain]:
        stmt = (
            self._scope_stmt(
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
            )
            .where(OfficialResultORM.bet_score_id.in_(bet_score_ids))
            .options(
                joinedload(OfficialResultORM.bet_context),
                joinedload(OfficialResultORM.event_session),
                joinedload(OfficialResultORM.testing_event_session),
                joinedload(OfficialResultORM.bet_score),
            )
        )

        rows = self._session.execute(stmt).scalars().all()

        return [
            OfficialResultDomain(
                id=row.id,
                bet_context_public_id=row.bet_context.public_id,
                event_session_public_id=row.event_session.public_id if row.event_session is not None else None,
                testing_event_session_public_id=(
                    row.testing_event_session.public_id
                    if row.testing_event_session is not None
                    else None
                ),
                bet_score_code=row.bet_score.code,
                label=row.bet_score.label,
                value=row.value,
                source=row.source,
                created_at=row.created_at,
            )
            for row in sorted(rows, key=lambda item: item.bet_score.code)
        ]

    def _scope_stmt(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
    ):
        stmt = select(OfficialResultORM).where(OfficialResultORM.bet_context_id == bet_context_id)

        if event_session_id is None:
            stmt = stmt.where(OfficialResultORM.event_session_id.is_(None))
        else:
            stmt = stmt.where(OfficialResultORM.event_session_id == event_session_id)

        if testing_event_session_id is None:
            stmt = stmt.where(OfficialResultORM.testing_event_session_id.is_(None))
        else:
            stmt = stmt.where(OfficialResultORM.testing_event_session_id == testing_event_session_id)

        return stmt