"""
聊天服务 - 使用重构后的 Agent
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent.companion_agent import CompanionAgent
from ..schemas.chat import ChatRequest, ChatResponse
from ..core.config import settings


class ChatService:
    """聊天服务 - 封装 Agent 调用"""
    
    def __init__(
        self,
        session: AsyncSession,
        openai_api_key: str = None,
        model: str = None,
        base_url: str = None,
    ):
        self.session = session
        self.agent = CompanionAgent(
            db=session,
            api_key=openai_api_key or settings.openai_api_key,
            model=model or settings.openai_model,
            base_url=base_url or settings.openai_base_url,
        )
    
    async def send_message(
        self,
        user_id: int,
        payload: ChatRequest
    ) -> ChatResponse:
        """发送消息并获取回复"""
        result = await self.agent.chat(
            user_id=user_id,
            message=payload.message,
            conversation_id=payload.conversation_id
        )
        
        return ChatResponse(
            reply=result["response"],
            conversation_id=result["conversation_id"],
            detected_emotion="neutral",  # TODO: 实现情感检测
            memories_used=result.get("memories_used", []),
        )
