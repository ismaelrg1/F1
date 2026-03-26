import resend

from app.core.config import settings
from app.domain.auth.ports import EmailSender

resend.api_key = settings.resend_api_key


class ResendEmailSender(EmailSender):
    def send_password_reset_email(self, *, to_email: str, reset_url: str) -> None:
        resend.Emails.send(
            {
                "from": self._from_address,
                "to": [to_email],
                "subject": self._password_reset_subject,
                "html": self._build_password_reset_html(reset_url),
                "text": self._build_password_reset_text(reset_url),
            }
        )

    @property
    def _from_address(self) -> str:
        return f"{settings.resend_from_name} <{settings.resend_from_email}>"

    @property
    def _password_reset_subject(self) -> str:
        return f"Reset your {settings.app_name} password"

    def _build_password_reset_text(self, reset_url: str) -> str:
        return (
            f"You requested a password reset for {settings.app_name}.\n\n"
            f"Open this link to choose a new password:\n{reset_url}\n\n"
            f"This link expires in {settings.password_reset_token_expire_minutes} minutes.\n"
            "If you did not request this, you can ignore this email."
        )

    def _build_password_reset_html(self, reset_url: str) -> str:
        return f"""
<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;color:#111827;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f4f6;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border-radius:16px;padding:40px 32px;">
            <tr>
              <td>
                <p style="margin:0 0 12px;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#6b7280;">
                  {settings.app_name}
                </p>
                <h1 style="margin:0 0 16px;font-size:28px;line-height:1.2;color:#111827;">
                  Reset your password
                </h1>
                <p style="margin:0 0 24px;font-size:16px;line-height:1.6;color:#374151;">
                  We received a request to reset the password for your account. Use the button below to choose a new one.
                </p>
                <p style="margin:0 0 28px;">
                  <a
                    href="{reset_url}"
                    style="display:inline-block;background:#111827;color:#ffffff;text-decoration:none;padding:14px 22px;border-radius:10px;font-size:15px;font-weight:600;"
                  >
                    Reset password
                  </a>
                </p>
                <p style="margin:0 0 16px;font-size:14px;line-height:1.6;color:#4b5563;">
                  This link expires in {settings.password_reset_token_expire_minutes} minutes.
                </p>
                <p style="margin:0 0 8px;font-size:14px;line-height:1.6;color:#4b5563;">
                  If the button does not work, copy and paste this link into your browser:
                </p>
                <p style="margin:0 0 24px;font-size:14px;line-height:1.6;word-break:break-all;">
                  <a href="{reset_url}" style="color:#2563eb;text-decoration:none;">{reset_url}</a>
                </p>
                <p style="margin:0;font-size:14px;line-height:1.6;color:#6b7280;">
                  If you did not request this, you can safely ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
