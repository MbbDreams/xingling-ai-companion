from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import User
from app.services.bootstrap import get_or_create_user

router = APIRouter()


# 模拟每日任务数据（后续可以存入数据库）
DEFAULT_TASKS = [
    {"id": 1, "title": "冥想放松", "description": "和晚星一起做5分钟冥想", "icon": "🧘", "reward_coins": 10},
    {"id": 2, "title": "AI绘画", "description": "让晚星为你画一幅画", "icon": "🎨", "reward_coins": 15},
    {"id": 3, "title": "写故事", "description": "和晚星共同创作一个故事", "icon": "📖", "reward_coins": 20},
    {"id": 4, "title": "旅行计划", "description": "规划一次虚拟旅行", "icon": "✈️", "reward_coins": 15},
    {"id": 5, "title": "知识问答", "description": "和晚星玩问答游戏", "icon": "❓", "reward_coins": 10},
]


@router.get("/tasks")
async def get_daily_tasks(
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取每日任务列表"""
    user = await get_or_create_user(session, user_id)
    
    # TODO: 从数据库获取用户今日任务完成状态
    # 目前返回默认任务，都标记为未完成
    tasks = [
        {
            "task_id": task["id"],
            "title": task["title"],
            "description": task["description"],
            "icon": task["icon"],
            "reward_coins": task["reward_coins"],
            "is_completed": False,
        }
        for task in DEFAULT_TASKS
    ]
    
    return {"tasks": tasks}


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """完成任务并获得奖励"""
    user = await get_or_create_user(session, user_id)
    
    # 查找任务
    task = next((t for t in DEFAULT_TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # TODO: 检查任务是否已完成（避免重复完成）
    # 目前直接发放奖励
    
    # 发放星币奖励
    reward = task["reward_coins"]
    user.coins += reward
    
    await session.flush()
    await session.commit()
    
    return {
        "success": True,
        "coins_earned": reward,
        "total_coins": user.coins,
        "message": f"完成任务！获得 {reward} 星币",
    }


@router.post("/wish")
async def make_wish(
    content: str,
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """许愿功能"""
    user = await get_or_create_user(session, user_id)
    
    # TODO: 将愿望保存到数据库
    # 目前只是返回成功消息
    
    return {
        "success": True,
        "message": "愿望已许下，晚星会帮你守护",
        "wish": content,
        "created_at": datetime.now().isoformat(),
    }
