from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import DiaryEntry
from app.schemas.diary import DiaryCalendarResponse, DiaryCreate, DiaryRead
from app.services.bootstrap import get_or_create_companion, get_or_create_user
from app.services.diary_service import DiaryService

router = APIRouter()


@router.get("/list", response_model=list[DiaryRead])
async def list_diaries(
    user_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> list[DiaryRead]:
    user = await get_or_create_user(session, user_id)
    companion = await get_or_create_companion(session, user)
    return await DiaryService(session).list_diaries(
        user.id, companion.id, start_date, end_date, page, page_size
    )


@router.post("", response_model=DiaryRead)
async def create_diary(
    payload: DiaryCreate,
    session: AsyncSession = Depends(get_db_session),
) -> DiaryRead:
    print(f"[DEBUG] Received payload: {payload}")
    print(f"[DEBUG] happened_on: {payload.happened_on}")
    user = await get_or_create_user(session, payload.user_id)
    companion = await get_or_create_companion(session, user, payload.companion_id)
    return await DiaryService(session).create_diary(user.id, companion.id, payload)


@router.get("/calendar", response_model=DiaryCalendarResponse)
async def get_diary_calendar(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> DiaryCalendarResponse:
    """获取某月的日记日历数据"""
    user = await get_or_create_user(session, user_id)
    companion = await get_or_create_companion(session, user)
    
    # 查询该月所有日记
    result = await session.execute(
        select(DiaryEntry)
        .where(
            DiaryEntry.user_id == user.id,
            DiaryEntry.companion_id == companion.id,
            extract("year", DiaryEntry.happened_on) == year,
            extract("month", DiaryEntry.happened_on) == month,
        )
        .order_by(DiaryEntry.happened_on.asc())
    )
    diaries = result.scalars().all()
    
    days = []
    for diary in diaries:
        days.append({
            "day": diary.happened_on.day,
            "mood": diary.mood,
            "has_diary": True,
        })
    
    return DiaryCalendarResponse(
        year=year,
        month=month,
        days=days,
    )
