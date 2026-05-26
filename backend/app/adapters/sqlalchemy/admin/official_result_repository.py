from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.betting import BetContext, BetScore
from app.db.competition import EventSession, TestingEventSession
from app.db.scoring import OfficialResult
from app.db.scoring.official_result import SourceType
from app.domain.admin.official_results.models import (
    AdminOfficialResult,
    AdminOfficialResultInput,
)
from app.domain.admin.official_results.ports import AdminOfficialResultRepository


class SqlAlchemyAdminOfficialResultRepository(AdminOfficialResultRepository):
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
        ).where(OfficialResult.bet_score_id.in_(bet_score_ids))

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
        ).where(OfficialResult.bet_score_id.in_(bet_score_ids))

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
        results: list[AdminOfficialResultInput],
        score_ids_by_code: dict[str, int],
    ) -> list[AdminOfficialResult]:
        rows: list[OfficialResult] = []

        for item in results:
            row = OfficialResult(
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
        results: list[AdminOfficialResultInput],
        score_ids_by_code: dict[str, int],
    ) -> list[AdminOfficialResult]:
        stmt = self._scope_stmt(
            bet_context_id=bet_context_id,
            event_session_id=event_session_id,
            testing_event_session_id=testing_event_session_id,
        ).options(joinedload(OfficialResult.bet_score))

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

    def _reload_results(
        self,
        *,
        bet_context_id: int,
        event_session_id: int | None,
        testing_event_session_id: int | None,
        bet_score_ids: set[int],
    ) -> list[AdminOfficialResult]:
        stmt = (
            self._scope_stmt(
                bet_context_id=bet_context_id,
                event_session_id=event_session_id,
                testing_event_session_id=testing_event_session_id,
            )
            .where(OfficialResult.bet_score_id.in_(bet_score_ids))
            .options(
                joinedload(OfficialResult.bet_context),
                joinedload(OfficialResult.event_session),
                joinedload(OfficialResult.testing_event_session),
                joinedload(OfficialResult.bet_score),
            )
        )

        rows = self._session.execute(stmt).scalars().all()

        return [
            AdminOfficialResult(
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