from datetime import datetime, date
from typing import List, Set

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_user_optional
from app.models import User, Companion
from app.services.bootstrap import get_or_create_user, get_or_create_companion

router = APIRouter()


# 模拟每日任务数据（后续可以存入数据库）
DEFAULT_TASKS = [
    {"id": 1, "title": "冥想放松", "description": "和晚星一起做5分钟冥想", "icon": "🧘", "reward_coins": 10, "intimacy": 5},
    {"id": 2, "title": "AI绘画", "description": "让晚星为你画一幅画", "icon": "🎨", "reward_coins": 15, "intimacy": 8},
    {"id": 3, "title": "写故事", "description": "和晚星共同创作一个故事", "icon": "📖", "reward_coins": 20, "intimacy": 10},
    {"id": 4, "title": "旅行计划", "description": "规划一次虚拟旅行", "icon": "✈️", "reward_coins": 15, "intimacy": 8},
    {"id": 5, "title": "知识问答", "description": "和晚星玩问答游戏", "icon": "❓", "reward_coins": 10, "intimacy": 5},
]

# 内存中存储今日已完成任务（实际应使用 Redis 或数据库）
# 格式: {user_id: {task_id: completed_date}}
_completed_tasks: dict[int, dict[int, date]] = {}


def _get_today_completed(user_id: int) -> Set[int]:
    """获取用户今日已完成的任务ID"""
    today = date.today()
    user_tasks = _completed_tasks.get(user_id, {})
    return {task_id for task_id, completed_date in user_tasks.items() if completed_date == today}


def _mark_task_completed(user_id: int, task_id: int):
    """标记任务为已完成"""
    if user_id not in _completed_tasks:
        _completed_tasks[user_id] = {}
    _completed_tasks[user_id][task_id] = date.today()


@router.get("/tasks")
async def get_daily_tasks(
    user: User = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取每日任务列表"""
    # 获取今日已完成的任务
    completed_task_ids = _get_today_completed(user.id)
    
    tasks = [
        {
            "task_id": task["id"],
            "title": task["title"],
            "description": task["description"],
            "icon": task["icon"],
            "reward_coins": task["reward_coins"],
            "is_completed": task["id"] in completed_task_ids,
        }
        for task in DEFAULT_TASKS
    ]
    
    return {"tasks": tasks}


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    user: User = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """完成任务并获得奖励"""
    # 查找任务
    task = next((t for t in DEFAULT_TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查任务是否已完成（防止重复完成）
    completed_task_ids = _get_today_completed(user.id)
    if task_id in completed_task_ids:
        raise HTTPException(status_code=400, detail="今日已完成该任务，请明天再来")
    
    # 标记任务为已完成
    _mark_task_completed(user.id, task_id)
    
    # 发放星币奖励
    reward = task["reward_coins"]
    user.coins += reward
    
    # 增加亲密度
    companion = await get_or_create_companion(session, user)
    intimacy_reward = task.get("intimacy", 5)
    companion.intimacy += intimacy_reward
    
    # 更新等级（每100亲密度升一级）
    new_level = int(companion.intimacy / 100) + 1
    companion.level = f"Lv.{new_level}"
    
    await session.flush()
    await session.commit()
    
    return {
        "success": True,
        "coins_earned": reward,
        "total_coins": user.coins,
        "intimacy_gained": intimacy_reward,
        "total_intimacy": companion.intimacy,
        "current_level": companion.level,
        "message": f"完成任务！获得 {reward} 星币，亲密度 +{intimacy_reward}",
    }


@router.post("/wish")
async def make_wish(
    body: dict,
    user: User = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """许愿功能"""
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="愿望内容不能为空")
    
    # TODO: 将愿望保存到数据库
    
    return {
        "success": True,
        "message": "愿望已许下，晚星会帮你守护",
        "wish": content,
        "created_at": datetime.now().isoformat(),
    }
