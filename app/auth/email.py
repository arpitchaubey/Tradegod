import smtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings

logger = logging.getLogger("auth_email")

class EmailService:
    """
    Asynchronous, non-blocking email delivery service for TradeGod authentication
    and transactional notifications (OTP verification, security alerts).
    """

    @classmethod
    def _send_sync(cls, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        if not settings.smtp_host or not settings.smtp_user:
            logger.info(
                f"ℹ️ [MOCK/DEV EMAIL DISPATCH] SMTP server not configured in .env. "
                f"Simulated email sent to '{to_email}' with subject: '{subject}'. "
                f"(To enable live delivery, configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env)"
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from_email or settings.smtp_user
            msg["To"] = to_email

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            if settings.smtp_use_tls:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10.0)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10.0)

            if settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)

            server.sendmail(msg["From"], [to_email], msg.as_string())
            server.quit()
            logger.info(f"✅ Email successfully delivered to {to_email} via {settings.smtp_host}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to deliver email to {to_email}: {e}")
            return False

    @classmethod
    async def send_email(cls, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Asynchronously dispatches email in a thread pool without blocking the async event loop."""
        return await asyncio.to_thread(cls._send_sync, to_email, subject, html_content, text_content)

    @classmethod
    async def send_password_reset_otp(cls, to_email: str, otp_code: str) -> bool:
        """Sends branded, secure 6-digit password reset verification OTP."""
        subject = "🔐 TradeGod — Your Password Reset Verification Code"
        
        text_content = (
            f"TradeGod Password Reset Request\n\n"
            f"Your 6-digit verification code is: {otp_code}\n\n"
            f"This code will expire in 15 minutes. If you did not request this password reset, please ignore this email or contact security immediately.\n\n"
            f"— TradeGod AI Trading Engine Security Team"
        )

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0e14; color: #f4f4f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 520px; margin: 0 auto; background-color: #12161f; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
    .header {{ text-align: center; margin-bottom: 24px; }}
    .logo-text {{ font-size: 18px; font-weight: 800; letter-spacing: 2px; color: #ffffff; text-transform: uppercase; }}
    .badge {{ display: inline-block; background-color: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); border-radius: 4px; font-size: 10px; font-weight: 700; padding: 2px 6px; margin-left: 6px; vertical-align: middle; }}
    .title {{ font-size: 20px; font-weight: 700; color: #ffffff; margin-top: 16px; margin-bottom: 8px; text-align: center; }}
    .subtitle {{ font-size: 13px; color: #a1a1aa; line-height: 1.5; text-align: center; margin-bottom: 28px; }}
    .otp-box {{ background: linear-gradient(135deg, rgba(37,99,235,0.1), rgba(147,51,234,0.1)); border: 1px solid rgba(59,130,246,0.3); border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0; }}
    .otp-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #93c5fd; font-weight: 600; margin-bottom: 8px; }}
    .otp-code {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #ffffff; text-shadow: 0 0 20px rgba(59,130,246,0.5); }}
    .expiry {{ font-size: 11px; color: #71717a; margin-top: 8px; }}
    .footer {{ border-top: 1px solid rgba(255,255,255,0.06); padding-top: 20px; margin-top: 28px; font-size: 11px; color: #71717a; line-height: 1.5; text-align: center; }}
    .warning {{ background-color: rgba(225,29,72,0.1); border-left: 3px solid #e11d48; padding: 10px 14px; border-radius: 6px; font-size: 11px; color: #fda4af; margin: 20px 0; text-align: left; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="logo-text">TRADE GOD</span>
      <span class="badge">QUANT</span>
    </div>
    <div class="title">Password Reset Verification</div>
    <div class="subtitle">We received a request to reset your TradeGod account password. Enter the 6-digit verification code below to set a new password.</div>
    
    <div class="otp-box">
      <div class="otp-label">Verification Code</div>
      <div class="otp-code">{otp_code}</div>
      <div class="expiry">⏱️ Valid for 15 minutes</div>
    </div>

    <div class="warning">
      🔒 <strong>Security Warning:</strong> If you did not request this verification code, please ignore this email. Never share this code with anyone.
    </div>

    <div class="footer">
      TradeGod Institutional Quantitative AI Signal Engine<br>
      Automated Security Notification &bull; Do not reply directly to this email
    </div>
  </div>
</body>
</html>
"""
        return await cls.send_email(to_email, subject, html_content, text_content)

email_service = EmailService()
