from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: str
    user_id: str | None
    user_email: str | None
    action: str
    category: str
    status: str
    ip_address: str | None
    device: str | None
    browser: str | None
    details: str | None
    created_at: datetime

    class Config:
        from_attributes = True
