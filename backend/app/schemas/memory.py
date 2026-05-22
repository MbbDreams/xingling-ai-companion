from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MemoryCreate(BaseModel):
    memory: str = Field(min_length=1, max_length=1000)
    category: str = "general"
    importance: float = Field(default=0.5, ge=0, le=1)
    user_id: int | None = None
    companion_id: int | None = None


class MemoryRead(BaseModel):
    id: int
    user_id: int
    companion_id: int | None = None
    memory: str
    category: str
    importance: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
