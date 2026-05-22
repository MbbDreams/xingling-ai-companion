from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.models import User
from app.services.auth_service import AuthService


# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[int]:
    """
    从 JWT Token 获取当前用户 ID
    返回 None 表示未登录（访客模式）
    """
    if credentials is None:
        return None
    
    try:
        payload = AuthService.verify_token(credentials.credentials, "access")
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        return int(user_id)
    except Exception:
        return None


async def get_current_user_optional(
    session: AsyncSession = Depends(get_db_session),
    user_id: Optional[int] = Depends(get_current_user_id),
) -> User:
    """
    获取当前用户，如果未登录则返回默认访客用户
    """
    if user_id is not None:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is not None:
            return user
    
    # 返回默认访客用户
    result = await session.scalars(
        select(User).where(User.auth_provider == "guest", User.provider_user_id == "local-dev")
    )
    user = result.first()
    if user is not None:
        return user
    
    # 创建默认用户
    user = User(nickname="Lee", auth_provider="guest", provider_user_id="local-dev")
    session.add(user)
    await session.flush()
    return user
