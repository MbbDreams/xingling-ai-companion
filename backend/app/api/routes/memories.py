from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import Memory
from app.schemas.memory import MemoryCreate, MemoryRead
from app.services.bootstrap import get_or_create_companion, get_or_create_user

router = APIRouter()


@router.get("/list", response_model=list[MemoryRead])
async def list_memories(
    user_id: int | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> list[Memory]:
    user = await get_or_create_user(session, user_id)
    
    query = select(Memory).where(Memory.user_id == user.id)
    
    if category:
        query = query.where(Memory.category == category)
    
    query = query.order_by(Memory.importance.desc(), Memory.created_at.desc())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await session.scalars(query)
    return list(result.all())


@router.post("", response_model=MemoryRead)
async def create_memory(
    payload: MemoryCreate,
    session: AsyncSession = Depends(get_db_session),
) -> Memory:
    user = await get_or_create_user(session, payload.user_id)
    companion = await get_or_create_companion(session, user, payload.companion_id)
    memory = Memory(
        user_id=user.id,
        companion_id=companion.id,
        memory=payload.memory,
        category=payload.category,
        importance=payload.importance,
    )
    session.add(memory)
    await session.flush()
    await session.commit()
    return memory


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """删除记忆"""
    user = await get_or_create_user(session, user_id)
    
    memory = await session.get(Memory, memory_id)
    if not memory or memory.user_id != user.id:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    await session.delete(memory)
    await session.commit()
    
    return {"detail": "记忆已删除"}
