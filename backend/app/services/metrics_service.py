from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.login_attempt import ApiRequestLog, LoginAttempt
from app.models.session import Session as UserSession
from app.models.user import User
from app.schemas.metrics import AnalyticsReport, CategoryCount, DashboardMetrics, TimeSeriesPoint

SEVERITY_WEIGHT = {"low": 1, "medium": 3, "high": 7, "critical": 15}


async def compute_dashboard_metrics(db: AsyncSession) -> DashboardMetrics:
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()

    active_sessions = (
        await db.execute(
            select(func.count())
            .select_from(UserSession)
            .where(UserSession.revoked.is_(False), UserSession.expires_at >= now)
        )
    ).scalar_one()

    successful_logins = (
        await db.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(LoginAttempt.success.is_(True), LoginAttempt.created_at >= day_ago)
        )
    ).scalar_one()

    failed_logins = (
        await db.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(LoginAttempt.success.is_(False), LoginAttempt.created_at >= day_ago)
        )
    ).scalar_one()

    open_alerts_result = await db.execute(
        select(Alert.severity, func.count()).where(Alert.status == "open").group_by(Alert.severity)
    )
    open_alert_counts = dict(open_alerts_result.all())
    open_alerts = sum(open_alert_counts.values())

    api_requests_24h = (
        await db.execute(select(func.count()).select_from(ApiRequestLog).where(ApiRequestLog.created_at >= day_ago))
    ).scalar_one()

    suspicious_events_24h = (
        await db.execute(select(func.count()).select_from(Alert).where(Alert.created_at >= day_ago))
    ).scalar_one()

    # Security score: start at 100, subtract weighted penalty for each open alert (floor 0).
    penalty = sum(SEVERITY_WEIGHT.get(sev, 1) * count for sev, count in open_alert_counts.items())
    security_score = max(0, 100 - penalty)

    if open_alert_counts.get("critical", 0) > 0:
        threat_level = "critical"
    elif open_alert_counts.get("high", 0) > 0:
        threat_level = "high"
    elif open_alert_counts.get("medium", 0) > 0:
        threat_level = "medium"
    else:
        threat_level = "low"

    return DashboardMetrics(
        total_users=total_users,
        active_sessions=active_sessions,
        successful_logins_24h=successful_logins,
        failed_logins_24h=failed_logins,
        security_score=security_score,
        threat_level=threat_level,
        open_alerts=open_alerts,
        api_requests_24h=api_requests_24h,
        suspicious_events_24h=suspicious_events_24h,
    )


async def compute_analytics_report(db: AsyncSession, days: int = 7) -> AnalyticsReport:
    now = datetime.now(timezone.utc)

    daily_login_activity: list[TimeSeriesPoint] = []
    failed_login_trend: list[TimeSeriesPoint] = []
    security_incidents: list[TimeSeriesPoint] = []
    system_performance: list[TimeSeriesPoint] = []

    for i in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        label = day_start.strftime("%b %d")

        success_count = (
            await db.execute(
                select(func.count()).select_from(LoginAttempt).where(
                    LoginAttempt.success.is_(True),
                    LoginAttempt.created_at >= day_start,
                    LoginAttempt.created_at < day_end,
                )
            )
        ).scalar_one()
        daily_login_activity.append(TimeSeriesPoint(label=label, value=success_count))

        fail_count = (
            await db.execute(
                select(func.count()).select_from(LoginAttempt).where(
                    LoginAttempt.success.is_(False),
                    LoginAttempt.created_at >= day_start,
                    LoginAttempt.created_at < day_end,
                )
            )
        ).scalar_one()
        failed_login_trend.append(TimeSeriesPoint(label=label, value=fail_count))

        incident_count = (
            await db.execute(
                select(func.count()).select_from(Alert).where(
                    Alert.created_at >= day_start, Alert.created_at < day_end
                )
            )
        ).scalar_one()
        security_incidents.append(TimeSeriesPoint(label=label, value=incident_count))

        avg_duration = (
            await db.execute(
                select(func.avg(ApiRequestLog.duration_ms)).where(
                    ApiRequestLog.created_at >= day_start, ApiRequestLog.created_at < day_end
                )
            )
        ).scalar_one()
        system_performance.append(TimeSeriesPoint(label=label, value=round(avg_duration or 0)))

    threat_categories_result = await db.execute(select(Alert.category, func.count()).group_by(Alert.category))
    threat_categories = [CategoryCount(category=cat, count=count) for cat, count in threat_categories_result.all()]

    severity_result = await db.execute(select(Alert.severity, func.count()).group_by(Alert.severity))
    alert_severity_breakdown = [
        CategoryCount(category=sev, count=count) for sev, count in severity_result.all()
    ]

    return AnalyticsReport(
        daily_login_activity=daily_login_activity,
        failed_login_trend=failed_login_trend,
        security_incidents=security_incidents,
        threat_categories=threat_categories,
        alert_severity_breakdown=alert_severity_breakdown,
        system_performance=system_performance,
    )
