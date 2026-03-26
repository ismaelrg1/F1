from passlib.context import CryptContext

from app.domain.auth.ports import PasswordHasher

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class PasslibPasswordHasher(PasswordHasher):
    def verify(self, plain_password: str, password_hash: str) -> bool:
        return pwd_context.verify(plain_password, password_hash)

    def hash(self, plain_password: str) -> str:
        return pwd_context.hash(plain_password)
