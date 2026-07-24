"""AI Security Analyst: answers natural-language questions about security
events by gathering real context from the database and asking Claude
(Anthropic API) to analyze it. Requires ANTHROPIC_API_KEY to be set; if it
is not, callers get a clear 503 rather than a silently fabricated answer.
"""
from datetime import datetime, timedelta, timezone

from anthropic import AsyncAnthropic
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert import Alert
from app.models.audit_log import AuditLog

SYSTEM_PROMPT = """You are the Sentinel AI Security Analyst, embedded in a cloud security and \
threat detection platform. You are given real, structured context pulled directly from the \
platform's database: recent security alerts and audit log entries. Analyze this data like an \
experienced security analyst would:
- Explain *why* something is suspicious in plain language.
- Reference specific alerts/logs from the provided context (severities, categories, timestamps, IPs) \
rather than speaking generically.
- When asked to recommend actions, give concrete, prioritized next steps a security analyst could take.
- When asked to summarize or generate an incident report, be concise and structured (use short sections).
- If the provided context does not contain enough information to answer confidently, say so explicitly \
rather than guessing.
Never invent alerts, users, or IP addresses that are not present in the supplied context."""


def _serialize_alert(alert: Alert) -> str:
    return (
        f"[Alert {alert.id[:8]}] severity={alert.severity} category={alert.category} "
        f"status={alert.status} user={alert.user.email if alert.user else 'n/a'} "
        f"source_ip={alert.source_ip} created_at={alert.created_at.isoformat()} "
        f"description={alert.description!r} notes={alert.notes!r}"
    )


def _serialize_log(log: AuditLog) -> str:
    return (
        f"[Log {log.id[:8]}] action={log.action} category={log.category} status={log.status} "
        f"user={log.user_email} ip={log.ip_address} device={log.device} browser={log.browser} "
        f"created_at={log.created_at.isoformat()}"
    )


async def _gather_context(db: AsyncSession, alert_id: str | None) -> dict:
    day_ago = datetime.now(timezone.utc) - timedelta(hours=24)

    recent_alerts_result = await db.execute(
        select(Alert).where(Alert.created_at >= day_ago).order_by(Alert.created_at.desc()).limit(25)
    )
    recent_alerts = recent_alerts_result.scalars().all()

    recent_logs_result = await db.execute(
        select(AuditLog).where(AuditLog.created_at >= day_ago).order_by(AuditLog.created_at.desc()).limit(50)
    )
    recent_logs = recent_logs_result.scalars().all()

    focus_alert = None
    if alert_id:
        focus_alert = await db.get(Alert, alert_id)

    return {
        "focus_alert": _serialize_alert(focus_alert) if focus_alert else None,
        "recent_alerts": [_serialize_alert(a) for a in recent_alerts],
        "recent_logs": [_serialize_log(log) for log in recent_logs],
        "counts": {
            "alerts_last_24h": len(recent_alerts),
            "logs_last_24h": len(recent_logs),
        },
    }


def _build_user_message(question: str, context: dict) -> str:
    parts = [f"Analyst question: {question}", ""]
    if context["focus_alert"]:
        parts.append("Alert in focus:")
        parts.append(context["focus_alert"])
        parts.append("")
    parts.append(f"Recent alerts (last 24h, {context['counts']['alerts_last_24h']} total):")
    parts.extend(context["recent_alerts"] or ["(none)"])
    parts.append("")
    parts.append(f"Recent audit log entries (last 24h, {context['counts']['logs_last_24h']} total):")
    parts.extend(context["recent_logs"] or ["(none)"])
    return "\n".join(parts)


async def ask_security_analyst(db: AsyncSession, *, question: str, alert_id: str | None = None) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Security Analyst is not configured: set ANTHROPIC_API_KEY in the backend environment.",
        )

    context = await _gather_context(db, alert_id)
    user_message = _build_user_message(question, context)

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    answer = "".join(block.text for block in response.content if block.type == "text")

    return {
        "answer": answer,
        "model": settings.ANTHROPIC_MODEL,
        "context_used": context["counts"] | {"focus_alert": bool(context["focus_alert"])},
    }
