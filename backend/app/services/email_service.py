"""Minimal email sender.

No real SMTP/SES integration is configured for this project (that requires
provider credentials only the deploying org can supply). In development this
simply logs the message; swap `send_email` for a real provider call (SES,
SendGrid, Postmark, etc.) in production, keeping this same function signature
so callers don't need to change.
"""
import logging

logger = logging.getLogger("sentinel.email")


def send_email(to: str, subject: str, body: str) -> None:
    logger.info("EMAIL -> to=%s subject=%r\n%s", to, subject, body)


def send_verification_email(to: str, token: str, frontend_url: str) -> None:
    link = f"{frontend_url}/verify-email?token={token}"
    send_email(to, "Verify your Sentinel account", f"Click to verify your email: {link}")


def send_password_reset_email(to: str, token: str, frontend_url: str) -> None:
    link = f"{frontend_url}/reset-password?token={token}"
    send_email(to, "Reset your Sentinel password", f"Click to reset your password: {link}")
