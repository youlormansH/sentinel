from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.core.permissions import VIEW_ALL_SECURITY_DATA, VIEW_ANALYTICS
from app.db.session import get_db
from app.models.user import User
from app.schemas.metrics import AnalyticsReport, DashboardMetrics
from app.services.metrics_service import compute_analytics_report, compute_dashboard_metrics

router = APIRouter(tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(VIEW_ALL_SECURITY_DATA)),
):
    return await compute_dashboard_metrics(db)


@router.get("/analytics", response_model=AnalyticsReport)
async def get_analytics(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(VIEW_ANALYTICS)),
):
    return await compute_analytics_report(db, days=days)
