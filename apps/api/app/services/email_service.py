"""
Email delivery service.
- Dev: Send via SMTP to Mailpit (localhost:1025)
- Prod: Send via Resend API
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


def _build_magic_link_html(magic_link_url: str) -> str:
    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
        <div style="background: #0a0a0a; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 40px; text-align: center;">
            <h1 style="color: white; font-size: 28px; font-weight: 900; font-style: italic; letter-spacing: -1px; margin: 0 0 8px;">
                IRON <span style="color: #ef4444;">MIND</span>
            </h1>
            <p style="color: #9ca3af; font-size: 13px; margin: 0 0 32px;">
                Access the Command Center
            </p>

            <a href="{magic_link_url}" 
               style="display: inline-block; background: white; color: black; padding: 16px 48px; 
                      border-radius: 12px; font-weight: 800; font-size: 12px; text-decoration: none; 
                      letter-spacing: 2px; text-transform: uppercase;">
                VERIFY &amp; LOGIN
            </a>

            <p style="color: #6b7280; font-size: 11px; margin: 32px 0 0; line-height: 1.5;">
                This link expires in 15 minutes.<br>
                If you didn't request this, you can safely ignore this email.
            </p>
        </div>
        <p style="color: #374151; font-size: 9px; text-align: center; margin-top: 24px; letter-spacing: 2px; text-transform: uppercase;">
            IRON MIND / STRATEGIC LEARNING SYSTEMS
        </p>
    </div>
    """


def send_magic_link_email(to_email: str, magic_link_url: str) -> None:
    """
    Send a magic link email. Routes to SMTP (Mailpit) in dev, Resend API in prod.
    """
    subject = "Iron Mind — Your Login Link"
    html_body = _build_magic_link_html(magic_link_url)

    if settings.ENV == "prod" and settings.RESEND_API_KEY:
        _send_via_resend(to_email, subject, html_body)
    else:
        _send_via_smtp(to_email, subject, html_body)


def _send_via_smtp(to_email: str, subject: str, html_body: str) -> None:
    """Send email via SMTP (Mailpit in dev)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        logger.info(f"Magic link email sent via SMTP to {to_email}")
    except Exception as e:
        logger.error(f"SMTP send failed for {to_email}: {e}")
        # Don't crash the request — the link was still logged
        raise


def _send_via_resend(to_email: str, subject: str, html_body: str) -> None:
    """Send email via Resend API (production)."""
    import resend

    resend.api_key = settings.RESEND_API_KEY

    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        logger.info(f"Magic link email sent via Resend to {to_email}")
    except Exception as e:
        logger.error(f"Resend send failed for {to_email}: {e}")
        raise
