from app.adapters.google.google_identity_verifier import GoogleIdTokenVerifier
from app.core.config import settings


def test_google_identity_verifier_uses_google_client_id(monkeypatch) -> None:
    captured = {}

    def fake_verify_oauth2_token(raw_id_token, request, client_id):
        captured["raw_id_token"] = raw_id_token
        captured["client_id"] = client_id
        captured["request_type"] = type(request).__name__
        return {
            "sub": "google-sub-1",
            "email": "alice@gmail.com",
            "email_verified": True,
        }

    monkeypatch.setattr("app.adapters.google.google_identity_verifier.id_token.verify_oauth2_token", fake_verify_oauth2_token)
    monkeypatch.setattr(settings, "google_client_id", "test-google-client-id")

    verifier = GoogleIdTokenVerifier()
    identity = verifier.verify("fake-google-token")

    assert captured["raw_id_token"] == "fake-google-token"
    assert captured["client_id"] == "test-google-client-id"
    assert captured["request_type"] == "Request"
    assert identity.sub == "google-sub-1"
    assert identity.email == "alice@gmail.com"
