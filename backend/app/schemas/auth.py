"""
认证相关的Pydantic模型
"""
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., description="手机号")
    purpose: str = Field(default="login", description="用途: login/register/reset_password")
    
    @validator("phone")
    def validate_phone(cls, v):
        # 清理空格和前缀
        phone = v.strip()
        for prefix in ["+86", "86"]:
            if phone.startswith(prefix):
                phone = phone[len(prefix):]
                break
        if not phone.isdigit() or len(phone) != 11:
            raise ValueError("手机号格式不正确")
        return phone


class VerifyCodeRequest(BaseModel):
    """验证验证码请求"""
    phone: str = Field(..., description="手机号")
    code: str = Field(..., description="验证码")
    
    @validator("phone")
    def validate_phone(cls, v):
        phone = v.strip()
        for prefix in ["+86", "86"]:
            if phone.startswith(prefix):
                phone = phone[len(prefix):]
                break
        return phone


class RegisterRequest(BaseModel):
    """注册请求"""
    phone: str = Field(..., description="手机号")
    code: str = Field(..., description="验证码")
    password: str = Field(..., min_length=6, max_length=20, description="密码")
    nickname: str = Field(..., min_length=1, max_length=30, description="昵称")
    avatar: str | None = Field(default=None, description="头像URL")
    
    @validator("phone")
    def validate_phone(cls, v):
        phone = v.strip()
        for prefix in ["+86", "86"]:
            if phone.startswith(prefix):
                phone = phone[len(prefix):]
                break
        return phone
    
    @validator("password")
    def validate_password(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        return v


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    code: str = Field(..., description="验证码")
    
    @validator("phone")
    def validate_phone(cls, v):
        phone = v.strip()
        for prefix in ["+86", "86"]:
            if phone.startswith(prefix):
                phone = phone[len(prefix):]
                break
        return phone


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(default=86400, description="过期时间(秒)")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class PhoneLoginRequest(BaseModel):
    """手机号一键登录请求（通过运营商网关验证）"""
    phone: str = Field(..., description="手机号")
    access_token: str = Field(..., description="运营商返回的access_token")
    operator: str = Field(default="cmcc", description="运营商: cmcc/unicom/telecom")


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: int
    phone: str = Field(..., description="手机号(脱敏显示)")
    nickname: str
    avatar: str | None = None
    email: str | None = None
    gender: str | None = None
    birthday: str | None = None
    bio: str | None = None
    location: str | None = None
    website: str | None = None
    coins: int = 0
    is_vip: bool = False
    vip_expire_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class UpdateProfileRequest(BaseModel):
    """更新资料请求"""
    nickname: str | None = Field(default=None, min_length=1, max_length=30)
    avatar: str | None = None
    email: str | None = None
    gender: str | None = Field(default=None, description="male/female/other")
    birthday: str | None = Field(default=None, description="格式: YYYY-MM-DD")
    bio: str | None = Field(default=None, max_length=200, description="个人简介")
    location: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=100)


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")
    
    @validator("new_password")
    def validate_password(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        return v
