from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models import Message
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    return await ChatService(session).send_message(payload)


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> ChatHistoryResponse:
    """获取聊天历史"""
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 获取总消息数
    count_result = await session.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    total = len(count_result.scalars().all())
    
    # 获取消息列表（倒序，最新的在后面）
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    messages = result.scalars().all()
    
    return ChatHistoryResponse(
        conversation_id=conversation_id,
        total=total,
        page=page,
        page_size=page_size,
        messages=[
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "emotion": msg.emotion,
                "created_at": msg.created_at,
            }
            for msg in messages
        ],
    )


@router.get("/suggestions")
async def get_chat_suggestions() -> dict:
    """获取快捷回复建议"""
    return {
        "suggestions": [
            {"text": "今天心情怎么样", "icon": "💬"},
            {"text": "陪我聊聊天", "icon": "🌙"},
            {"text": "我想听故事", "icon": "📖"},
            {"text": "帮我放松一下", "icon": "🧘"},
            {"text": "分享今天的趣事", "icon": "✨"},
        ]
    }
