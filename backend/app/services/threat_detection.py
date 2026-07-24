"""Automated security monitoring: brute force, impossible travel, API abuse.

Each detector is intentionally simple and explainable (rule-based, not ML) so
its behavior is auditable — a requirement for a security product. Every
detector that fires creates an Alert, bumps the involved user's threat_score,
and broadcasts a `new_alert` event over the WebSocket hub for the live
dashboard.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timeutils import ensure_utc
from app.models.alert import Alert
from app.models.login_attempt import ApiRequestLog, LoginAttempt
from app.models.user import User
from app.services.geo import GeoLocation
from app.ws.manager import manager

EARTH_RADIUS_KM = 6371.0




def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


async def _create_alert(
    db: AsyncSession,
    *,
    severity: str,
    category: str,
    description: str,
    user_id: str | None,
    source_ip: str | None,
) -> Alert:
    alert = Alert(
        severity=severity,
        category=category,
        description=description,
        user_id=user_id,
        source_ip=source_ip,
        status="open",
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    await manager.broadcast(
        "new_alert",
        {
            "id": alert.id,
            "severity": alert.severity,
            "category": alert.category,
            "description": alert.description,
            "created_at": alert.created_at,
        },
    )
    return alert


async def _bump_threat_score(db: AsyncSession, user_id: str, amount: int) -> None:
    user = await db.get(User, user_id)
    if user:
        user.threat_score = min(100, user.threat_score + amount)
        await db.commit()


async def check_brute_force(db: AsyncSession, *, email: str, ip_address: str) -> Alert | None:
    """10+ failed logins from one IP within the configured window."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=settings.BRUTE_FORCE_WINDOW_MINUTES)
    stmt = select(func.count()).select_from(LoginAttempt).where(
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.success.is_(False),
        LoginAttempt.created_at >= window_start,
    )
    failed_count = (await db.execute(stmt)).scalar_one()

    if failed_count < settings.BRUTE_FORCE_ATTEMPT_THRESHOLD:
        return None

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    alert = await _create_alert(
        db,
        severity="critical",
        category="brute_force",
        description=(
            f"{failed_count} failed login attempts detected from IP {ip_address} "
            f"within {settings.BRUTE_FORCE_WINDOW_MINUTES} minutes (target: {email})."
        ),
        user_id=user.id if user else None,
        source_ip=ip_address,
    )
    if user:
        await _bump_threat_score(db, user.id, 25)
    return alert


async def check_impossible_travel(
    db: AsyncSession,
    *,
    user: User,
    new_location: GeoLocation,
    login_time: datetime,
    ip_address: str,
) -> Alert | None:
    """Flag logins that imply physically impossible travel speed since the last login."""
    if not user.last_login_at or user.last_login_country is None:
        return None

    # Reconstruct the previous login's coordinates from the most recent successful attempt.
    stmt = (
        select(LoginAttempt)
        .where(LoginAttempt.user_id == user.id, LoginAttempt.success.is_(True))
        .order_by(LoginAttempt.created_at.desc())
        .offset(1)
        .limit(1)
    )
    prev_attempt = (await db.execute(stmt)).scalar_one_or_none()
    if not prev_attempt or prev_attempt.latitude is None:
        return None

    elapsed_hours = (ensure_utc(login_time) - ensure_utc(prev_attempt.created_at)).total_seconds() / 3600.0
    if elapsed_hours <= 0:
        elapsed_hours = 1 / 3600.0  # avoid div-by-zero; treat as ~1 second

    distance_km = _haversine_km(
        prev_attempt.latitude, prev_attempt.longitude, new_location.latitude, new_location.longitude
    )
    implied_speed_kmh = distance_km / elapsed_hours

    if implied_speed_kmh <= settings.IMPOSSIBLE_TRAVEL_MAX_KMH or distance_km < 300:
        return None

    alert = await _create_alert(
        db,
        severity="high",
        category="impossible_travel",
        description=(
            f"Suspicious login location detected for {user.email}: "
            f"{prev_attempt.city}, {prev_attempt.country} -> {new_location.city}, {new_location.country} "
            f"({distance_km:.0f} km in {elapsed_hours * 60:.1f} min, implied speed "
            f"{implied_speed_kmh:.0f} km/h)."
        ),
        user_id=user.id,
        source_ip=ip_address,
    )
    await _bump_threat_score(db, user.id, 20)
    return alert


async def check_api_abuse(db: AsyncSession, *, user_id: str | None, ip_address: str) -> Alert | None:
    """Excessive API request volume from a single user/IP within the configured window."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=settings.API_ABUSE_WINDOW_MINUTES)
    conditions = [ApiRequestLog.created_at >= window_start, ApiRequestLog.ip_address == ip_address]
    stmt = select(func.count()).select_from(ApiRequestLog).where(*conditions)
    request_count = (await db.execute(stmt)).scalar_one()

    if request_count < settings.API_ABUSE_REQUEST_THRESHOLD:
        return None

    # Avoid re-alerting every single request once already flagged in this window.
    recent_alert_stmt = select(func.count()).select_from(Alert).where(
        Alert.category == "api_abuse",
        Alert.source_ip == ip_address,
        Alert.created_at >= window_start,
    )
    if (await db.execute(recent_alert_stmt)).scalar_one() > 0:
        return None

    alert = await _create_alert(
        db,
        severity="medium",
        category="api_abuse",
        description=(
            f"Excessive API activity detected: {request_count} requests from IP {ip_address} "
            f"within {settings.API_ABUSE_WINDOW_MINUTES} minutes."
        ),
        user_id=user_id,
        source_ip=ip_address,
    )
    if user_id:
        await _bump_threat_score(db, user_id, 10)
    return alert
