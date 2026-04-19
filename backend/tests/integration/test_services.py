from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.adapters.sqlalchemy.auth.auth_repository import SqlAlchemyAuthRepository
from app.adapters.sqlalchemy.public.season_repository import SqlAlchemySeasonRepository
from app.domain.auth import (
    GoogleIdentity,
    LoginGoogleUser,
    LoginLocalUser,
    RegisterGoogleUser,
    RegisterLocalUser,
    RequestPasswordReset,
    ResetPassword,
)

from app.domain.seasons import GetActiveSeason, ListSeasons


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def all(self):
        return self._value


class FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return FakeScalarResult(self._value)


class FakeSession:
    def __init__(self, execute_values=None, get_values=None):
        self.execute_values = list(execute_values or [])
        self.get_values = list(get_values or [])
        self.added = []

    def execute(self, _stmt):
        value = self.execute_values.pop(0)
        return FakeExecuteResult(value)

    def get(self, _model, _id):
        return self.get_values.pop(0)

    def add(self, value):
        self.added.append(value)

    def flush(self):
        if self.added:
            self.added[-1].id = 99


class FakePasswordHasher:
    def verify(self, plain_password: str, password_hash: str) -> bool:
        return plain_password == f"verified:{password_hash}"

    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"


class FakeGoogleVerifier:
    def __init__(self, identity: GoogleIdentity):
        self.identity = identity

    def verify(self, _id_token: str) -> GoogleIdentity:
        return self.identity


class FakeResetTokenHasher:
    def hash(self, raw_token: str) -> str:
        return f"token-hash:{raw_token}"


class FakeEmailSender:
    def __init__(self):
        self.sent = []

    def send_password_reset_email(self, *, to_email: str, reset_url: str) -> None:
        self.sent.append({"to_email": to_email, "reset_url": reset_url})


class FakePasswordResetTokenRepository:
    def __init__(self):
        self.active_by_user_id = {}
        self.records_by_hash = {}

    def get_active_for_user(self, user_id: int):
        return self.active_by_user_id.get(user_id)

    def invalidate_active_for_user(self, user_id: int, *, invalidated_at: datetime) -> None:
        record = self.active_by_user_id.get(user_id)
        if record is None:
            return
        updated = SimpleNamespace(**record.__dict__)
        updated.invalidated_at = invalidated_at
        self.records_by_hash[updated.token_hash] = updated
        self.active_by_user_id.pop(user_id, None)

    def create_token(self, *, user_id: int, token_hash: str, expires_at: datetime) -> None:
        record = SimpleNamespace(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used_at=None,
            invalidated_at=None,
            created_at=datetime.now(UTC),
        )
        self.active_by_user_id[user_id] = record
        self.records_by_hash[token_hash] = record

    def get_by_token_hash(self, token_hash: str):
        return self.records_by_hash.get(token_hash)

    def mark_as_used(self, token_hash: str, *, used_at: datetime) -> None:
        record = self.records_by_hash.get(token_hash)
        if record is None:
            return
        record.used_at = used_at
        self.active_by_user_id.pop(record.user_id, None)


class FakeAuthRepository:
    def __init__(self):
        self.users_by_username = {}
        self.users_by_email = {}
        self.users_by_google_sub = {}
        self.next_id = 1

    def get_by_username(self, username: str):
        return self.users_by_username.get(username)

    def get_by_id(self, user_id: int):
        for user in self.users_by_email.values():
            if user.id == user_id:
                return user
        return None

    def get_by_email(self, email: str):
        return self.users_by_email.get(email)

    def get_by_google_sub(self, google_sub: str):
        return self.users_by_google_sub.get(google_sub)

    def create_local_user(self, *, username: str, email: str, password_hash: str):
        user = SimpleNamespace(
            id=self.next_id,
            public_id=uuid4(),
            username=username,
            email=email,
            password_hash=password_hash,
            google_sub=None,
            auth_provider="LOCAL",
        )
        self.next_id += 1
        self.users_by_username[username] = user
        self.users_by_email[email] = user
        return user

    def create_google_user(self, *, username: str, email: str, google_sub: str):
        user = SimpleNamespace(
            id=self.next_id,
            public_id=uuid4(),
            username=username,
            email=email,
            password_hash=None,
            google_sub=google_sub,
            auth_provider="GOOGLE",
        )
        self.next_id += 1
        self.users_by_username[username] = user
        self.users_by_email[email] = user
        self.users_by_google_sub[google_sub] = user
        return user

    def update_password(self, *, user_id: int, password_hash: str) -> None:
        user = self.get_by_id(user_id)
        if user is None:
            return
        user.password_hash = password_hash
        user.auth_provider = "LOCAL"


def test_login_user_authenticates_matching_password() -> None:
    user = SimpleNamespace(
        id=1,
        public_id=uuid4(),
        username="alice",
        email="a@example.com",
        password_hash="secret",
        google_sub=None,
        auth_provider="LOCAL",
    )
    repository = SqlAlchemyAuthRepository(FakeSession(execute_values=[user]))
    use_case = LoginLocalUser(repository, FakePasswordHasher())

    result = use_case.execute("alice", "verified:secret")

    assert result.id == 1
    assert result.username == "alice"


def test_register_local_user_hashes_password_and_creates_user() -> None:
    repository = FakeAuthRepository()
    use_case = RegisterLocalUser(repository, FakePasswordHasher())

    result = use_case.execute(username="alice", email="a@example.com", password="secret")

    assert result.id == 1
    assert result.username == "alice"
    assert result.password_hash == "hashed:secret"


def test_register_google_user_creates_google_account() -> None:
    repository = FakeAuthRepository()
    verifier = FakeGoogleVerifier(
        GoogleIdentity(sub="google-sub-1", email="alice@gmail.com", email_verified=True)
    )
    use_case = RegisterGoogleUser(repository, verifier)

    result = use_case.execute("fake-id-token")

    assert result.id == 1
    assert result.email == "alice@gmail.com"
    assert result.google_sub == "google-sub-1"


def test_login_google_user_resolves_registered_account() -> None:
    repository = FakeAuthRepository()
    user = SimpleNamespace(
        id=1,
        public_id=uuid4(),
        username="alice",
        email="alice@gmail.com",
        password_hash=None,
        google_sub="google-sub-1",
        auth_provider="GOOGLE",
    )
    repository.users_by_google_sub["google-sub-1"] = user
    verifier = FakeGoogleVerifier(
        GoogleIdentity(sub="google-sub-1", email="alice@gmail.com", email_verified=True)
    )
    use_case = LoginGoogleUser(repository, verifier)

    result = use_case.execute("fake-id-token")

    assert result.id == 1
    assert result.auth_provider == "GOOGLE"


def test_request_password_reset_creates_hashed_token_and_sends_email() -> None:
    repository = FakeAuthRepository()
    user = repository.create_local_user(
        username="alice",
        email="a@example.com",
        password_hash="hashed:old",
    )
    token_repository = FakePasswordResetTokenRepository()
    email_sender = FakeEmailSender()
    use_case = RequestPasswordReset(
        repository,
        token_repository,
        FakeResetTokenHasher(),
        email_sender,
        reset_base_url="https://frontend/reset-password",
        token_ttl=timedelta(minutes=5),
        request_cooldown=timedelta(seconds=60),
    )

    use_case.execute(user.email)

    active = token_repository.get_active_for_user(user.id)
    assert active is not None
    assert active.token_hash.startswith("token-hash:")
    assert email_sender.sent
    assert email_sender.sent[0]["to_email"] == user.email
    assert email_sender.sent[0]["reset_url"].startswith("https://frontend/reset-password?token=")


def test_reset_password_updates_password_and_marks_token_used() -> None:
    repository = FakeAuthRepository()
    user = repository.create_local_user(
        username="alice",
        email="a@example.com",
        password_hash="hashed:old",
    )
    token_repository = FakePasswordResetTokenRepository()
    token_hash = "token-hash:raw-token"
    token_repository.records_by_hash[token_hash] = SimpleNamespace(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        used_at=None,
        invalidated_at=None,
        created_at=datetime.now(UTC),
    )
    use_case = ResetPassword(
        repository,
        token_repository,
        FakeResetTokenHasher(),
        FakePasswordHasher(),
    )

    use_case.execute(token="raw-token", new_password="new-secret")

    assert repository.get_by_id(user.id).password_hash == "hashed:new-secret"
    assert token_repository.records_by_hash[token_hash].used_at is not None


def test_season_use_cases_list_and_resolve_active_season() -> None:
    season_2026 = SimpleNamespace(id=1, year=2026, is_active=True)
    season_2025 = SimpleNamespace(id=2, year=2025, is_active=False)
    repository = SqlAlchemySeasonRepository(FakeSession(execute_values=[[season_2026, season_2025], season_2026]))

    seasons = ListSeasons(repository).execute()
    active = GetActiveSeason(repository).execute()

    assert [season.year for season in seasons] == [2026, 2025]
    assert active is not None
    assert active.id == season_2026.id
    assert active.year == season_2026.year
    assert active.is_active is season_2026.is_active
