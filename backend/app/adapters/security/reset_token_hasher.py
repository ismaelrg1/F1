import hashlib
from app.domain.auth.ports import ResetTokenHasher


class Sha256ResetTokenHasher(ResetTokenHasher):
    @staticmethod
    def hash(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()