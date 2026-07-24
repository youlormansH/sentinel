from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pyotp
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.permissions import ROLE_USER
from app.core.security import (
    create_token,
    decrypt_value,
    encrypt_value,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.timeutils import ensure_utc
from app.models.login_attempt import LoginAttempt
from app.models.rbac import Role
from app.models.session import Session as UserSession
from app.models.token import EmailVerificationToken, PasswordResetToken
from app.models.user import User
from app.services import geo
from app.services.audit_service import write_audit_log
from app.services.email_service import send_password_reset_email, send_verification_email
from app.services.request_meta import RequestMeta
from app.services.threat_detection import check_brute_force, check_impossible_travel


class AuthError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


async def register_user(db: AsyncSession, *, email: str, full_name: str, password: str) -> User:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise AuthError("An account with this email already exists.")

    role_result = await db.execute(select(Role).where(Role.name == ROLE_USER))
    role = role_result.scalar_one_or_none()
    if role is None:
        raise AuthError("Default role not seeded; run the database seed script.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    user = User(email=email, full_name=full_name, password_hash=hash_password(password), role_id=role.id)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = hash_token_pair()
    verification = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verification)
    await db.commit()
    send_verification_email(user.email, token, settings.FRONTEND_URL)

    await write_audit_log(
        db, action="user.registered", category="account", user_id=user.id, user_email=user.email
    )
    return user


def hash_token_pair() -> str:
    from app.core.security import generate_secure_token

    return generate_secure_token()


async def verify_email(db: AsyncSession, token: str) -> None:
    token_hash = hash_token(token)
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if not record or record.used or ensure_utc(record.expires_at) < datetime.now(timezone.utc):
        raise AuthError("Invalid or expired verification token.")

    user = await db.get(User, record.user_id)
    if not user:
        raise AuthError("User not found.")

    user.is_email_verified = True
    record.used = True
    await db.commit()


async def authenticate(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    mfa_code: str | None,
    meta: RequestMeta,
) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    location = geo.resolve_ip(meta.ip_address)
    success = False
    failure_reason: str | None = None

    try:
        if user is None or not verify_password(password, user.password_hash):
            failure_reason = "invalid_credentials"
            raise AuthError("Incorrect email or password.", status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            failure_reason = "account_disabled"
            raise AuthError("This account has been disabled.", status.HTTP_403_FORBIDDEN)

        if user.mfa_enabled:
            if not mfa_code:
                return {"mfa_required": True, "user": user}
            secret = decrypt_value(user.mfa_secret_encrypted)
            totp = pyotp.TOTP(secret)
            if not totp.verify(mfa_code, valid_window=1):
                failure_reason = "invalid_mfa_code"
                raise AuthError("Invalid MFA code.", status.HTTP_401_UNAUTHORIZED)

        success = True
        return {"mfa_required": False, "user": user}
    finally:
        login_time = datetime.now(timezone.utc)
        attempt = LoginAttempt(
            email=email,
            user_id=user.id if user else None,
            success=success,
            ip_address=meta.ip_address,
            user_agent=meta.user_agent,
            country=location.country,
            city=location.city,
            latitude=location.latitude,
            longitude=location.longitude,
            failure_reason=failure_reason,
        )
        db.add(attempt)
        await db.commit()

        await write_audit_log(
            db,
            action="user.login",
            category="authentication",
            status="successful" if success else "failed",
            user_id=user.id if user else None,
            user_email=email,
            ip_address=meta.ip_address,
            device=meta.device,
            browser=meta.browser,
            details=failure_reason,
        )

        if not success:
            await check_brute_force(db, email=email, ip_address=meta.ip_address)
        elif user:
            await check_impossible_travel(
                db, user=user, new_location=location, login_time=login_time, ip_address=meta.ip_address
            )
            user.last_login_at = login_time
            user.last_login_ip = meta.ip_address
            user.last_login_country = location.country
            await db.commit()


async def issue_token_pair(db: AsyncSession, *, user: User, meta: RequestMeta) -> dict:
    access_token, _, _ = create_token(user.id, "access", extra_claims={"role": user.role.name})
    refresh_token, refresh_expires, jti = create_token(user.id, "refresh")

    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        jti=jti,
        ip_address=meta.ip_address,
        user_agent=meta.user_agent,
        device=meta.device,
        expires_at=refresh_expires,
    )
    db.add(session)
    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def refresh_access_token(db: AsyncSession, *, refresh_token: str) -> dict:
    from app.core.security import decode_token

    try:
        payload = decode_token(refresh_token)
    except ValueError as exc:
        raise AuthError("Invalid or expired refresh token.", status.HTTP_401_UNAUTHORIZED) from exc

    if payload.get("type") != "refresh":
        raise AuthError("Invalid token type.", status.HTTP_401_UNAUTHORIZED)

    token_hash = hash_token(refresh_token)
    result = await db.execute(select(UserSession).where(UserSession.refresh_token_hash == token_hash))
    session = result.scalar_one_or_none()
    if not session or session.revoked or ensure_utc(session.expires_at) < datetime.now(timezone.utc):
        raise AuthError("Session expired or revoked. Please log in again.", status.HTTP_401_UNAUTHORIZED)

    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise AuthError("User not found or disabled.", status.HTTP_401_UNAUTHORIZED)

    # Rotate refresh token to limit replay window.
    session.revoked = True
    new_refresh_token, new_expires, new_jti = create_token(user.id, "refresh")
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(new_refresh_token),
        jti=new_jti,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        device=session.device,
        expires_at=new_expires,
    )
    db.add(new_session)

    access_token, _, _ = create_token(user.id, "access", extra_claims={"role": user.role.name})
    await db.commit()

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


async def logout(db: AsyncSession, *, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    result = await db.execute(select(UserSession).where(UserSession.refresh_token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session:
        session.revoked = True
        await db.commit()


async def request_password_reset(db: AsyncSession, *, email: str) -> None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return  # do not reveal whether the account exists

    token = hash_token_pair()
    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset)
    await db.commit()
    send_password_reset_email(user.email, token, settings.FRONTEND_URL)


async def reset_password(db: AsyncSession, *, token: str, new_password: str) -> None:
    token_hash = hash_token(token)
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    record = result.scalar_one_or_none()
    if not record or record.used or ensure_utc(record.expires_at) < datetime.now(timezone.utc):
        raise AuthError("Invalid or expired reset token.")

    user = await db.get(User, record.user_id)
    if not user:
        raise AuthError("User not found.")

    user.password_hash = hash_password(new_password)
    record.used = True

    # Revoke all existing sessions on password change.
    sessions = await db.execute(select(UserSession).where(UserSession.user_id == user.id, UserSession.revoked.is_(False)))
    for session in sessions.scalars():
        session.revoked = True

    await db.commit()
    await write_audit_log(db, action="user.password_reset", category="account", user_id=user.id, user_email=user.email)


async def setup_mfa(db: AsyncSession, *, user: User) -> dict:
    secret = pyotp.random_base32()
    user.mfa_secret_encrypted = encrypt_value(secret)
    await db.commit()
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(name=user.email, issuer_name="Sentinel")
    return {"secret": secret, "otpauth_url": otpauth_url}


async def enable_mfa(db: AsyncSession, *, user: User, code: str) -> None:
    if not user.mfa_secret_encrypted:
        raise AuthError("Call /auth/mfa/setup first.")
    secret = decrypt_value(user.mfa_secret_encrypted)
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise AuthError("Invalid MFA code.")
    user.mfa_enabled = True
    await db.commit()
    await write_audit_log(db, action="user.mfa_enabled", category="account", user_id=user.id, user_email=user.email)


async def disable_mfa(db: AsyncSession, *, user: User, code: str) -> None:
    if not user.mfa_enabled or not user.mfa_secret_encrypted:
        raise AuthError("MFA is not enabled.")
    secret = decrypt_value(user.mfa_secret_encrypted)
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise AuthError("Invalid MFA code.")
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    await db.commit()
    await write_audit_log(db, action="user.mfa_disabled", category="account", user_id=user.id, user_email=user.email)
