"""
认证相关API路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session, get_current_user_id
from app.models import User
from app.services.auth_service import AuthService, VerificationCodeStore, SMSService
from app.schemas.auth import (
    SendCodeRequest, VerifyCodeRequest,
    RegisterRequest, LoginRequest,
    TokenResponse, RefreshTokenRequest,
    UserInfoResponse, UpdateProfileRequest,
    ChangePasswordRequest
)


router = APIRouter(tags=["认证"])


def mask_phone(phone: str) -> str:
    """脱敏手机号"""
    return f"{phone[:3]}****{phone[-4:]}"


# ============ 发送验证码 ============

@router.post("/send-code", summary="发送验证码")
async def send_verification_code(
    request: SendCodeRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    发送验证码到手机号
    - 未注册手机号会同时注册
    - 验证码5分钟内有效
    - 同一手机号60秒内不能重复发送
    """
    # 生成验证码
    code = AuthService.generate_verification_code()
    
    # 存储验证码
    VerificationCodeStore.store(request.phone, code, request.purpose)
    
    # 发送短信
    result = await SMSService.send_verification_code(request.phone, code)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {
        "success": True,
        "message": "验证码已发送",
        # 开发环境返回验证码，方便测试
        "debug_code": code if True else None  # TODO: 生产环境关闭
    }


# ============ 注册 ============

@router.post("/register", summary="注册", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    注册新用户
    1. 验证验证码
    2. 创建用户
    3. 返回Token
    """
    # 验证验证码
    if not VerificationCodeStore.verify(request.phone, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )
    
    # 检查手机号是否已注册
    result = await session.execute(
        select(User).where(User.phone == request.phone)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已注册，请直接登录"
        )
    
    # 创建用户
    user = User(
        phone=request.phone,
        nickname=request.nickname,
        avatar=request.avatar,
        auth_provider="phone",
        hashed_password=AuthService.hash_password(request.password),
        coins=100,  # 新用户赠送100星币
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # 生成Token
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ============ 登录 ============

@router.post("/login", summary="登录", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    手机号+验证码登录
    1. 验证验证码
    2. 查找或创建用户
    3. 返回Token
    """
    # 验证验证码
    if not VerificationCodeStore.verify(request.phone, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )
    
    # 查找用户，不存在则自动注册
    result = await session.execute(
        select(User).where(User.phone == request.phone)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # 自动注册（使用手机号作为昵称）
        user = User(
            phone=request.phone,
            nickname=f"用户{request.phone[-4:]}",
            auth_provider="phone",
            coins=100,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await session.commit()
    
    # 生成Token
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ============ 刷新Token ============

@router.post("/refresh", summary="刷新Token", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """使用refresh_token获取新的access_token"""
    payload = AuthService.verify_token(request.refresh_token, "refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh_token已过期或无效"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token"
        )
    
    # 验证用户存在
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    # 生成新Token
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    new_refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


# ============ 获取当前用户信息 ============

@router.get("/me", summary="获取当前用户信息", response_model=UserInfoResponse)
async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    """获取当前登录用户的信息"""
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录"
        )
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return UserInfoResponse(
        id=user.id,
        phone=mask_phone(user.phone) if user.phone else "",
        nickname=user.nickname or f"用户{user.phone[-4:] if user.phone else '0000'}",
        avatar=user.avatar,
        email=user.email,
        gender=user.gender,
        birthday=user.birthday.strftime("%Y-%m-%d") if user.birthday else None,
        bio=user.bio,
        location=user.location,
        website=user.website,
        coins=user.coins,
        is_vip=user.is_vip,
        vip_expire_at=user.vip_expire_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ============ 更新个人资料 ============

@router.put("/me", summary="更新个人资料", response_model=UserInfoResponse)
async def update_profile(
    request: UpdateProfileRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    """更新当前用户的个人资料"""
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录"
        )
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    # 更新字段
    if request.nickname is not None:
        user.nickname = request.nickname
    if request.avatar is not None:
        user.avatar = request.avatar
    if request.email is not None:
        user.email = request.email
    if request.gender is not None:
        if request.gender not in ["male", "female", "other"]:
            raise HTTPException(status_code=400, detail="性别值无效")
        user.gender = request.gender
    if request.birthday is not None:
        try:
            user.birthday = datetime.strptime(request.birthday, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="生日格式错误，应为YYYY-MM-DD")
    if request.bio is not None:
        user.bio = request.bio
    if request.location is not None:
        user.location = request.location
    if request.website is not None:
        user.website = request.website
    
    user.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(user)
    
    return UserInfoResponse(
        id=user.id,
        phone=mask_phone(user.phone) if user.phone else "",
        nickname=user.nickname or f"用户{user.phone[-4:] if user.phone else '0000'}",
        avatar=user.avatar,
        email=user.email,
        gender=user.gender,
        birthday=user.birthday.strftime("%Y-%m-%d") if user.birthday else None,
        bio=user.bio,
        location=user.location,
        website=user.website,
        coins=user.coins,
        is_vip=user.is_vip,
        vip_expire_at=user.vip_expire_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ============ 修改密码 ============

@router.post("/change-password", summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    """修改当前用户的密码"""
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录"
        )
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该账户未设置密码，请使用验证码登录"
        )
    
    # 验证原密码
    if not AuthService.verify_password(request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 更新密码
    user.hashed_password = AuthService.hash_password(request.new_password)
    user.updated_at = datetime.utcnow()
    await session.commit()
    
    return {"success": True, "message": "密码修改成功"}


# ============ 退出登录 ============

@router.post("/logout", summary="退出登录")
async def logout(
    user_id: int = Depends(get_current_user_id)
):
    """
    退出登录
    前端应清除本地存储的token
    后端可以在这里实现token黑名单（需要Redis）
    """
    return {"success": True, "message": "已退出登录"}
