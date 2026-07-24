import math
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.core.permissions import VIEW_LOGS
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogOut
from app.schemas.common import Page

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=Page[AuditLogOut])
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(VIEW_LOGS)),
):
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    filters = []
    if search:
        pattern = f"%{search}%"
        filters.append((AuditLog.user_email.ilike(pattern)) | (AuditLog.action.ilike(pattern)))
    if category:
        filters.append(AuditLog.category == category)
    if status_filter:
        filters.append(AuditLog.status == status_filter)
    if start_date:
        filters.append(AuditLog.created_at >= start_date)
    if end_date:
        filters.append(AuditLog.created_at <= end_date)

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    logs = (await db.execute(stmt)).scalars().all()

    return Page(
        items=[AuditLogOut.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
