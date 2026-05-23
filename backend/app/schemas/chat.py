from datetime import datetime
from typing import List, Optional

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
    """聊天响应"""
    reply: str                              # AI 回复
    conversation_id: int                    # 会话 ID
    detected_emotion: str = "neutral"       # 检测到的情绪
    memories_used: List[str] = []           # 使用的记忆
    intimacy_gained: int = 1                # 获得的亲密度


class ChatHistoryResponse(BaseModel):
    conversation_id: int
    total: int
    page: int
    page_size: int
    messages: list[MessageRead]


class CreateConversationResponse(BaseModel):
    """创建会话响应"""
    conversation_id: int
    title: str | None = None
    created_at: datetime
