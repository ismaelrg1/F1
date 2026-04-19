from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from app.db.auth import PasswordResetToken

from app.domain.auth.models import PasswordResetTokenRecord

from app.domain.auth.ports import PasswordResetTokenRepository

class SqlAlchemyPasswordResetTokenRepository(PasswordResetTokenRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_active_for_user(self, user_id: int) -> PasswordResetTokenRecord | None:
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .where(PasswordResetToken.used_at.is_(None))
            .where(PasswordResetToken.invalidated_at.is_(None))
            .where(PasswordResetToken.expires_at > func.now())
            .order_by(PasswordResetToken.created_at.desc())
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        return None if row is None else self._map_token_record(row)

    def invalidate_active_for_user(self, user_id: int, *, invalidated_at: datetime) -> None:
        stmt = (
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .where(PasswordResetToken.used_at.is_(None))
            .where(PasswordResetToken.invalidated_at.is_(None))
            .values(invalidated_at=invalidated_at)
        )
        self._session.execute(stmt)

    def create_token(self, *, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            PasswordResetToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )

    def get_by_token_hash(self, token_hash: str) -> PasswordResetTokenRecord | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        row = self._session.execute(stmt).scalar_one_or_none()
        return None if row is None else self._map_token_record(row)


    def mark_as_used(self, token_hash: str, *, used_at: datetime) -> None:
        stmt = (
            update(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .values(used_at=used_at)
        )
        self._session.execute(stmt)

    @staticmethod
    def _map_token_record(row: PasswordResetToken) -> PasswordResetTokenRecord:
        return PasswordResetTokenRecord(
            user_id=row.user_id,
            token_hash=row.token_hash,
            expires_at=row.expires_at,
            used_at=row.used_at,
            invalidated_at=row.invalidated_at,
            created_at=row.created_at,
        )
