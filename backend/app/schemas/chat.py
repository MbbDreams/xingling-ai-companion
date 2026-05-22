from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    user_id: int | None = None
    companion_id: int | None = None
    conversation_id: int | None = None


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    emotion: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    emotion: str
    memory_candidates: list[str]
    messages: list[MessageRead]
    intimacy_gained: int = 1  # 本次对话获得的亲密度


class ChatHistoryResponse(BaseModel):
    conversation_id: int
    total: int
    page: int
    page_size: int
    messages: list[MessageRead]
