import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.core.permissions import MANAGE_ALERTS, VIEW_ALL_SECURITY_DATA
from app.db.session import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertCreateRequest, AlertOut, AlertUpdateRequest
from app.schemas.common import Page
from app.services.audit_service import write_audit_log
from app.services.request_meta import extract_request_meta
from app.ws.manager import manager

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=Page[AlertOut])
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: str | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(VIEW_ALL_SECURITY_DATA)),
):
    stmt = select(Alert)
    count_stmt = select(func.count()).select_from(Alert)

    filters = []
    if severity:
        filters.append(Alert.severity == severity)
    if category:
        filters.append(Alert.category == category)
    if status_filter:
        filters.append(Alert.status == status_filter)
    if search:
        filters.append(Alert.description.ilike(f"%{search}%"))

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    alerts = (await db.execute(stmt)).scalars().all()

    return Page(
        items=[AlertOut.model_validate(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.post("", response_model=AlertOut, status_code=201)
async def create_alert(
    payload: AlertCreateRequest,
    db: AsyncSession = Depends(get_db),
    analyst: User = Depends(require_permissions(MANAGE_ALERTS)),
):
    alert = Alert(
        severity=payload.severity,
        category=payload.category,
        description=payload.description,
        user_id=payload.user_id,
        source_ip=payload.source_ip,
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
    return AlertOut.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertOut)
async def update_alert(
    request: Request,
    alert_id: str,
    payload: AlertUpdateRequest,
    db: AsyncSession = Depends(get_db),
    analyst: User = Depends(require_permissions(MANAGE_ALERTS)),
):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if payload.status is not None:
        alert.status = payload.status
        if payload.status == "resolved":
            alert.resolved_by_id = analyst.id
    if payload.notes is not None:
        alert.notes = payload.notes
    if payload.severity is not None:
        alert.severity = payload.severity

    await db.commit()
    await db.refresh(alert)

    meta = extract_request_meta(request)
    await write_audit_log(
        db,
        action="alert.updated",
        category="incident_response",
        user_id=analyst.id,
        user_email=analyst.email,
        ip_address=meta.ip_address,
        device=meta.device,
        browser=meta.browser,
        details=f"Alert {alert.id} -> status={alert.status}",
    )
    await manager.broadcast(
        "alert_updated",
        {"id": alert.id, "status": alert.status, "severity": alert.severity},
    )
    return AlertOut.model_validate(alert)
