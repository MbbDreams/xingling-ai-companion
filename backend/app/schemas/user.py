from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanionRead(BaseModel):
    id: int
    user_id: int
    name: str
    persona: str
    voice_style: str
    intimacy: int
    level: str
    mood: str | None = None
    online: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    """完整的用户信息（Profile 用）"""
    id: int
    nickname: str
    avatar: str | None = None
    email: str | None = None
    gender: str | None = None
    birthday: date | None = None
    bio: str | None = None
    location: str | None = None
    website: str | None = None
    coins: int = 100
    is_vip: bool = False
    vip_expire_at: datetime | None = None
    auth_provider: str = "guest"
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    user: UserRead
    companion: CompanionRead


class UpdateProfileRequest(BaseModel):
    """更新个人资料请求"""
    nickname: str | None = Field(None, min_length=1, max_length=30, description="昵称")
    avatar: str | None = Field(None, description="头像URL")
    email: str | None = Field(None, max_length=255, description="邮箱")
    gender: str | None = Field(None, description="性别: male/female/other")
    birthday: str | None = Field(None, description="生日: YYYY-MM-DD")
    bio: str | None = Field(None, max_length=200, description="个人简介")
    location: str | None = Field(None, max_length=50, description="所在地")
    website: str | None = Field(None, max_length=100, description="个人网站")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
