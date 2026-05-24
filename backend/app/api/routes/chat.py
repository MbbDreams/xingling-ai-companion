from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_user_id
from app.core.config import settings
from app.models import Message, Conversation, Companion
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse, CreateConversationResponse
from app.services.chat_service import ChatService
from app.services.chat_service_streaming import StreamingChatService

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> ChatResponse:
    """标准聊天接口（非流式）"""
    # 如果没有 user_id，使用默认用户 ID 1
    uid = user_id or 1
    
    service = ChatService(
        session,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url or None
    )
    return await service.send_message(uid, payload)


@router.post("/send/stream")
async def send_chat_message_stream(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> StreamingResponse:
    """
    流式聊天接口
    
    使用 SSE (Server-Sent Events) 实现流式输出
    首字响应时间 < 100ms
    """
    uid = user_id or 1
    
    service = StreamingChatService(
        session,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url or None
    )
    
    return StreamingResponse(
        service.stream_chat(uid, payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


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
                "is_from_user": msg.role == "user",  # 添加布尔字段供前端使用
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


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> CreateConversationResponse:
    """创建新的聊天会话"""
    uid = user_id or 1
    
    # 获取或创建用户的伴侣
    result = await session.execute(
        select(Companion).where(Companion.user_id == uid)
    )
    companion = result.scalar_one_or_none()
    
    if not companion:
        # 创建默认伴侣
        companion = Companion(
            user_id=uid,
            name="晚星",
            personality="温柔体贴的AI伴侣",
        )
        session.add(companion)
        await session.flush()
    
    # 创建新会话
    conversation = Conversation(
        user_id=uid,
        companion_id=companion.id,
        title="新的聊天",
    )
    session.add(conversation)
    await session.commit()
    
    return CreateConversationResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
    )
