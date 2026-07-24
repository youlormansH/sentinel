from pydantic import BaseModel


class AiQueryRequest(BaseModel):
    question: str
    alert_id: str | None = None


class AiQueryResponse(BaseModel):
    answer: str
    model: str
    context_used: dict
