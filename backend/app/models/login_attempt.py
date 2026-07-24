from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UUIDMixin


class LoginAttempt(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "login_attempts"

    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    success: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ApiRequestLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "api_request_logs"

    user_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
