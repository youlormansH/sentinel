from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_users: int
    active_sessions: int
    successful_logins_24h: int
    failed_logins_24h: int
    security_score: int
    threat_level: str
    open_alerts: int
    api_requests_24h: int
    suspicious_events_24h: int


class TimeSeriesPoint(BaseModel):
    label: str
    value: int


class CategoryCount(BaseModel):
    category: str
    count: int


class AnalyticsReport(BaseModel):
    daily_login_activity: list[TimeSeriesPoint]
    failed_login_trend: list[TimeSeriesPoint]
    security_incidents: list[TimeSeriesPoint]
    threat_categories: list[CategoryCount]
    alert_severity_breakdown: list[CategoryCount]
    system_performance: list[TimeSeriesPoint]
