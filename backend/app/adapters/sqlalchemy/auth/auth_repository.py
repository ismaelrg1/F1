from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.auth import User
from app.domain.auth.models import AuthenticatedLoginUser
from app.domain.auth.ports import (
    AuthRepository,
)

class SqlAlchemyAuthRepository(AuthRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, user_id: int) -> AuthenticatedLoginUser | None:
        stmt = select(User).where(User.id == user_id)
        user = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain_user(user)

    def get_by_username(self, username: str) -> AuthenticatedLoginUser | None:
        stmt = select(User).where(User.username == username)
        user = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain_user(user)

    def get_by_google_sub(self, google_sub: str) -> AuthenticatedLoginUser | None:
        stmt = select(User).where(User.google_sub == google_sub)
        user = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain_user(user)

    def create_local_user(self, *, username: str, password_hash: str) -> AuthenticatedLoginUser:
        user = User(
            username=username,
            password_hash=password_hash,
            auth_provider="LOCAL",
        )
        self._session.add(user)
        self._session.flush()
        return self._to_domain_user(user)

    def create_google_user(self, *, username: str, google_sub: str) -> AuthenticatedLoginUser:
        user = User(
            username=username,
            google_sub=google_sub,
            auth_provider="GOOGLE",
        )
        self._session.add(user)
        self._session.flush()
        return self._to_domain_user(user)

    def update_password(self, *, user_id: int, password_hash: str) -> None:
        stmt = select(User).where(User.id == user_id)
        user = self._session.execute(stmt).scalar_one_or_none()
        if user is None:
            return
        user.password_hash = password_hash
        user.auth_provider = "LOCAL"
        self._session.flush()

    @staticmethod
    def _to_domain_user(user: User | None) -> AuthenticatedLoginUser | None:
        if user is None:
            return None
        return AuthenticatedLoginUser(
            id=user.id,
            public_id=user.public_id,
            username=user.username,
            password_hash=user.password_hash,
            google_sub=user.google_sub,
            auth_provider=user.auth_provider,
        )
