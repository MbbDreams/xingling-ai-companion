from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Companion, User


async def get_or_create_user(session: AsyncSession, user_id: int | None = None) -> User:
    if user_id is not None:
        user = await session.get(User, user_id)
        if user is not None:
            return user

    result = await session.scalars(
        select(User).where(User.auth_provider == "guest", User.provider_user_id == "local-dev")
    )
    user = result.first()
    if user is not None:
        return user

    user = User(nickname="Lee", auth_provider="guest", provider_user_id="local-dev")
    session.add(user)
    await session.flush()
    return user


async def get_or_create_companion(
    session: AsyncSession,
    user: User,
    companion_id: int | None = None,
) -> Companion:
    if companion_id is not None:
        companion = await session.get(Companion, companion_id)
        if companion is not None and companion.user_id == user.id:
            return companion

    result = await session.scalars(select(Companion).where(Companion.user_id == user.id).limit(1))
    companion = result.first()
    if companion is not None:
        return companion

    companion = Companion(
        user_id=user.id,
        name="晚星",
        persona="温柔、敏感、会长期记住用户生活细节的 AI 陪伴者。",
        voice_style="warm",
        intimacy=82,
        level="Lv.6",
    )
    session.add(companion)
    await session.flush()
    return companion
