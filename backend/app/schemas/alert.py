from datetime import datetime

from pydantic import BaseModel, Field


class AlertOut(BaseModel):
    id: str
    severity: str
    category: str
    description: str
    user_id: str | None
    source_ip: str | None
    status: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCreateRequest(BaseModel):
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    category: str
    description: str
    user_id: str | None = None
    source_ip: str | None = None


class AlertUpdateRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(open|investigating|resolved|dismissed)$")
    notes: str | None = None
    severity: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
