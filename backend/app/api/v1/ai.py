from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.core.permissions import INVESTIGATE_THREATS
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import AiQueryRequest, AiQueryResponse
from app.services.ai_analyst import ask_security_analyst

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/query", response_model=AiQueryResponse)
async def query_ai_analyst(
    payload: AiQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(INVESTIGATE_THREATS)),
):
    result = await ask_security_analyst(db, question=payload.question, alert_id=payload.alert_id)
    return AiQueryResponse(**result)
