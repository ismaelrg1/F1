import pytest

from app.adapters.email import ResendEmailSender
from app.core.config import settings


def test_resend_email_sender_builds_password_reset_email_payload(monkeypatch) -> None:
    captured = {}

    def fake_send(payload):
        captured["payload"] = payload
        return {"id": "email_123"}

    monkeypatch.setattr("app.adapters.email.resend_email_sender.resend.Emails.send", fake_send)
    monkeypatch.setattr(settings, "app_name", "FutureF1")
    monkeypatch.setattr(settings, "password_reset_token_expire_minutes", 5)
    monkeypatch.setattr(settings, "resend_from_name", "FutureF1")
    monkeypatch.setattr(settings, "resend_from_email", "no-reply@futuref1.app")

    sender = ResendEmailSender()
    reset_url = "https://app.futuref1.com/reset-password?token=abc123"

    sender.send_password_reset_email(
        to_email="alice@example.com",
        reset_url=reset_url,
    )

    payload = captured["payload"]
    assert payload["from"] == "FutureF1 <no-reply@futuref1.app>"
    assert payload["to"] == ["alice@example.com"]
    assert payload["subject"] == "Reset your FutureF1 password"
    assert reset_url in payload["html"]
    assert reset_url in payload["text"]
    assert "expires in 5 minutes" in payload["html"]
    assert "expires in 5 minutes" in payload["text"]


@pytest.mark.manual
def test_send_real_password_reset_email() -> None:
    sender = ResendEmailSender()
    sender.send_password_reset_email(
        to_email="isrug1202@gmail.com",
        reset_url="http://localhost:3000/reset-password?token=manual-test-token",
    )
