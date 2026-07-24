from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, Base, TimestampMixin, UUIDMixin


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), default="general", index=True)
    status: Mapped[str] = mapped_column(String(20), default="successful")  # successful | failed

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device: Mapped[str | None] = mapped_column(String(255), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(255), nullable=True)

    details: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user: Mapped["User | None"] = relationship(lazy="selectin")  # noqa: F821
