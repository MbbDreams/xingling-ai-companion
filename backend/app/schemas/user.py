from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanionRead(BaseModel):
    id: int
    user_id: int
    name: str
    persona: str
    voice_style: str
    intimacy: int
    level: str

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    nickname: str
    avatar: str | None = None
    auth_provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    user: UserRead
    companion: CompanionRead
