from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    action: str,
    category: str = "general",
    status: str = "successful",
    user_id: str | None = None,
    user_email: str | None = None,
    ip_address: str | None = None,
    device: str | None = None,
    browser: str | None = None,
    details: str | None = None,
    commit: bool = True,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action,
        category=category,
        status=status,
        ip_address=ip_address,
        device=device,
        browser=browser,
        details=details,
    )
    db.add(log)
    if commit:
        await db.commit()
        await db.refresh(log)
    return log
