from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiaryEntry
from app.schemas.diary import DiaryCreate, DiaryRead


class DiaryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_diaries(
        self,
        user_id: int,
        companion_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[DiaryRead]:
        query = select(DiaryEntry).where(
            DiaryEntry.user_id == user_id,
            DiaryEntry.companion_id == companion_id,
        )
        
        if start_date:
            query = query.where(DiaryEntry.happened_on >= start_date)
        if end_date:
            query = query.where(DiaryEntry.happened_on <= end_date)
            
        query = query.order_by(DiaryEntry.happened_on.desc(), DiaryEntry.created_at.desc())
        
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        diaries = result.scalars().all()
        
        return [DiaryRead.model_validate(d) for d in diaries]

    async def create_diary(
        self,
        user_id: int,
        companion_id: int,
        payload: DiaryCreate,
    ) -> DiaryRead:
        happened_on = payload.happened_on or date.today()
        
        print(f"[DEBUG] Creating diary with happened_on: {happened_on}, payload: {payload}")
        
        diary = DiaryEntry(
            user_id=user_id,
            companion_id=companion_id,
            mood=payload.mood,
            content=payload.content,
            happened_on=happened_on,
        )
        
        self.session.add(diary)
        await self.session.flush()
        await self.session.refresh(diary)
        await self.session.commit()
        
        return DiaryRead.model_validate(diary)
