"""
个人中心相关API路由
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session, get_current_user_id, get_current_user_optional
from app.models import User, Companion
from app.schemas.user import (
    ProfileResponse, UserRead, CompanionRead,
    UpdateProfileRequest, ChangePasswordRequest
)
from app.services.auth_service import AuthService
from app.services.bootstrap import get_or_create_companion


router = APIRouter()


def mask_phone(phone: str) -> str:
    """脱敏手机号"""
    if not phone:
        return ""
    return f"{phone[:3]}****{phone[-4:]}"


@router.get("/me", summary="获取个人资料", response_model=ProfileResponse)
async def get_profile(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user_optional),
):
    """获取当前用户的完整资料（含伴侣信息）"""
    companion = await get_or_create_companion(session, user)
    await session.commit()
    return ProfileResponse(user=user, companion=companion)


@router.put("/me", summary="更新个人资料", response_model=UserRead)
async def update_profile(
    request: UpdateProfileRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    """更新当前用户的个人资料"""
    if user_id is None:
        raise HTTPException(status_code=401, detail="请先登录")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    if request.nickname is not None:
        user.nickname = request.nickname
    if request.avatar is not None:
        user.avatar = request.avatar
    if request.email is not None:
        user.email = request.email
    if request.gender is not None:
        if request.gender not in ("male", "female", "other"):
            raise HTTPException(status_code=400, detail="性别值无效")
        user.gender = request.gender
    if request.birthday is not None:
        try:
            user.birthday = datetime.strptime(request.birthday, "%Y-%m-%d").date()
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
    return user


@router.put("/companion/appearance", summary="更新伴侣外观")
async def update_companion_appearance(
    outfit_id: int | None = None,
    scene_id: int | None = None,
    voice_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user_optional),
):
    """更新伴侣的服装/场景/语音"""
    companion = await get_or_create_companion(session, user)

    if outfit_id is not None:
        companion.current_outfit_id = outfit_id
    if scene_id is not None:
        companion.current_scene_id = scene_id

    await session.commit()
    await session.refresh(companion)
    return {"success": True, "companion": CompanionRead.model_validate(companion)}


@router.post("/change-password", summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    """修改当前用户密码"""
    if user_id is None:
        raise HTTPException(status_code=401, detail="请先登录")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="该账户未设置密码，请使用验证码登录")

    if not AuthService.verify_password(request.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    user.hashed_password = AuthService.hash_password(request.new_password)
    user.updated_at = datetime.utcnow()
    await session.commit()

    return {"success": True, "message": "密码修改成功"}


@router.get("/stats", summary="获取账户统计")
async def get_stats(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user_optional),
):
    """获取用户的统计数据（消息数、记忆数、日记数等）"""
    from app.models import Message, Memory, DiaryEntry, Conversation

    # 消息总数
    conv_result = await session.execute(
        select(Conversation.id).where(Conversation.user_id == user.id)
    )
    conv_ids = [row[0] for row in conv_result.all()]

    total_messages = 0
    if conv_ids:
        msg_result = await session.execute(
            select(Message).where(Message.conversation_id.in_(conv_ids))
        )
        total_messages = len(msg_result.all())

    # 记忆数
    mem_result = await session.execute(
        select(Memory).where(Memory.user_id == user.id)
    )
    total_memories = len(mem_result.all())

    # 日记数
    diary_result = await session.execute(
        select(DiaryEntry).where(DiaryEntry.user_id == user.id)
    )
    total_diaries = len(diary_result.all())

    # 伴侣亲密度
    companion = await get_or_create_companion(session, user)

    return {
        "total_messages": total_messages,
        "total_memories": total_memories,
        "total_diaries": total_diaries,
        "intimacy_level": companion.level,
        "intimacy_points": companion.intimacy,
        "companion_name": companion.name,
    }
