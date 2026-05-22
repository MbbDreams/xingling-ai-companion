from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.user import ProfileResponse
from app.services.bootstrap import get_or_create_companion, get_or_create_user

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ProfileResponse:
    user = await get_or_create_user(session, user_id)
    companion = await get_or_create_companion(session, user)
    await session.commit()
    return ProfileResponse(user=user, companion=companion)
