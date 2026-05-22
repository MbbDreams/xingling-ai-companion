from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import GrowthMilestone, User, Companion
from app.schemas.growth import GrowthSummary, MilestoneResponse

router = APIRouter()


@router.get("/summary", response_model=GrowthSummary)
async def get_growth_summary(
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> GrowthSummary:
    """获取用户和伴侣的成长数据汇总"""
    # 获取或创建用户
    if user_id:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    else:
        result = await session.execute(select(User).order_by(User.id).limit(1))
        user = result.scalar_one_or_none()
    
    if not user:
        # 创建默认用户
        user = User(nickname="Lee", coins=100)
        session.add(user)
        companion = Companion(
            user_id=user.id if user.id else 1,
            name="晚星",
            intimacy=0,
            level="Lv.1",
        )
        session.add(companion)
        await session.commit()
        await session.refresh(user)
    
    # 获取或创建伴侣
    result = await session.execute(
        select(Companion).where(Companion.user_id == user.id)
    )
    companion = result.scalar_one_or_none()
    
    if not companion:
        companion = Companion(
            user_id=user.id,
            name="晚星",
            intimacy=0,
            level="Lv.1",
        )
        session.add(companion)
        await session.commit()
        await session.refresh(companion)
    
    # 计算等级（每100亲密度升一级）
    level = int(companion.intimacy / 100) + 1
    intimacy_for_next = 100 - (companion.intimacy % 100)
    
    # 获取里程碑数量
    result = await session.execute(
        select(func.count(GrowthMilestone.id))
        .where(GrowthMilestone.user_id == user.id)
    )
    milestones_count = result.scalar() or 0
    
    return GrowthSummary(
        intimacy_level=level,
        intimacy_points=companion.intimacy,
        intimacy_for_next=intimacy_for_next,
        total_messages=0,  # 可以从messages表统计
        milestones_count=milestones_count,
        active_days=0,  # 可以从统计表获取
    )


@router.get("/milestones", response_model=list[MilestoneResponse])
async def get_milestones(
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[MilestoneResponse]:
    """获取用户的里程碑列表"""
    if user_id:
        result = await session.execute(
            select(GrowthMilestone)
            .where(GrowthMilestone.user_id == user_id)
            .order_by(GrowthMilestone.achieved_at.desc())
        )
    else:
        result = await session.execute(
            select(GrowthMilestone)
            .order_by(GrowthMilestone.achieved_at.desc())
            .limit(20)
        )
    
    milestones = result.scalars().all()
    return [
        MilestoneResponse(
            id=m.id,
            title=m.title,
            description=m.description,
            achieved_at=m.achieved_at,
        )
        for m in milestones
    ]
