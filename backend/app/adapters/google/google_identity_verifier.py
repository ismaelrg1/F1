from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app.core.config import settings
from app.domain.auth import GoogleIdentity, GoogleIdentityVerifier, InvalidGoogleTokenError


class GoogleIdTokenVerifier(GoogleIdentityVerifier):
    def verify(self, raw_id_token: str) -> GoogleIdentity:
        try:
            payload = id_token.verify_oauth2_token(
                raw_id_token,
                Request(),
                settings.google_client_id,
            )
        except Exception as exc:
            raise InvalidGoogleTokenError() from exc

        email = payload.get("email")
        subject = payload.get("sub")
        email_verified = bool(payload.get("email_verified"))

        if not subject or not email:
            raise InvalidGoogleTokenError()

        return GoogleIdentity(
            sub=subject,
            email=email,
            email_verified=email_verified,
        )
