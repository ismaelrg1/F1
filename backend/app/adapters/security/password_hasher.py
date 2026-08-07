from werkzeug.security import check_password_hash, generate_password_hash

from app.domain.auth.ports import PasswordHasher

class WerkzeugPasswordHasher(PasswordHasher):
    def verify(self, plain_password: str, password_hash: str) -> bool:
        return check_password_hash(password_hash, plain_password)

    def hash(self, plain_password: str) -> str:
        return generate_password_hash(
            plain_password,
            method="scrypt",
        )
