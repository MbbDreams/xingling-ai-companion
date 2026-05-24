"""
流式聊天服务 - SSE 流式输出
"""
import json
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent.companion_agent import CompanionAgent
from ..schemas.chat import ChatRequest, ChatResponse
from ..core.config import settings


class StreamingChatService:
    """流式聊天服务"""
    
    def __init__(
        self,
        session: AsyncSession,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
    ):
        self.session = session
        self.agent = CompanionAgent(
            db=session,
            api_key=api_key or settings.llm_api_key,
            model=model or settings.llm_model,
            base_url=base_url or settings.llm_base_url,
        )
    
    async def stream_chat(
        self,
        user_id: int,
        payload: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天
        
        使用 SSE 格式返回数据
        """
        # 发送思考状态
        yield self._format_event("thinking", {"content": "晚星正在思考..."})
        
        try:
            # 流式获取回复
            async for chunk in self.agent.chat_stream(
                user_id=user_id,
                message=payload.message,
                conversation_id=payload.conversation_id
            ):
                yield self._format_event("content", {"content": chunk})
            
            # 发送完成事件
            yield self._format_event("complete", {"content": ""})
            
        except Exception as e:
            yield self._format_event("error", {"content": str(e)})
    
    def _format_event(self, event_type: str, data: dict) -> str:
        """格式化 SSE 事件"""
        return f"data: {json.dumps({'type': event_type, **data})}\n\n"
