"""
对话管理器 - 管理多轮对话上下文

职责：
1. 维护对话历史（数据库持久化）
2. 自动拼接上下文给 LLM
3. 对话摘要生成（长对话压缩）
4. 会话管理
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.entities import Conversation, Message


class ConversationManager:
    """
    对话管理器 - 核心上下文管理
    
    设计原则：
    1. 每个用户有多个会话（Conversation）
    2. 每个会话包含多条消息（Message）
    3. 自动加载历史消息作为上下文
    4. 长对话自动摘要压缩
    """
    
    # 最大保留的消息条数（防止 token 超限）
    MAX_MESSAGES = 20
    
    # 触发摘要的消息阈值
    SUMMARY_THRESHOLD = 15
    
    def __init__(self, db: AsyncSession, llm_client=None):
        self.db = db
        self.llm_client = llm_client
    
    async def get_or_create_conversation(
        self, 
        user_id: int, 
        conversation_id: Optional[int] = None
    ) -> Conversation:
        """获取或创建会话"""
        if conversation_id:
            result = await self.db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user_id
                    )
                )
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation
        
        # 创建新会话（companion_id 默认为 1）
        conversation = Conversation(
            user_id=user_id,
            companion_id=1,  # 默认伴侣 ID
            title="新对话"
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
    
    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        emotion: Optional[str] = None
    ) -> Message:
        """添加消息到会话"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            emotion=emotion
        )
        self.db.add(message)
        
        # 更新会话时间
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_conversation_history(
        self,
        conversation_id: int,
        limit: int = None
    ) -> List[Dict[str, str]]:
        """
        获取对话历史，格式化为 LLM 输入格式
        
        返回: [{"role": "user/assistant", "content": "..."}]
        """
        limit = limit or self.MAX_MESSAGES
        
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        messages = result.scalars().all()
        
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history
    
    async def build_llm_messages(
        self,
        conversation_id: int,
        user_message: str,
        system_prompt: str,
        memories: List[str] = None
    ) -> List[Dict[str, str]]:
        """
        构建 LLM 输入消息列表
        
        包含：
        1. System Prompt（含记忆）
        2. 历史对话
        3. 当前用户消息
        """
        messages = []
        
        # 1. System Prompt
        system_content = system_prompt
        if memories:
            memory_text = "\n".join([f"- {m}" for m in memories[:5]])
            system_content += f"\n\n【关于用户的重要记忆】\n{memory_text}"
        
        messages.append({"role": "system", "content": system_content})
        
        # 2. 历史对话
        history = await self.get_conversation_history(conversation_id)
        messages.extend(history)
        
        # 3. 当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def summarize_conversation(
        self,
        conversation_id: int
    ) -> str:
        """
        生成长对话摘要
        
        当对话超过阈值时，将早期对话压缩为摘要
        """
        if not self.llm_client:
            return ""
        
        # 获取早期消息
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(self.SUMMARY_THRESHOLD)
        )
        messages = result.scalars().all()
        
        if len(messages) < self.SUMMARY_THRESHOLD:
            return ""
        
        # 构建摘要请求
        conversation_text = "\n".join([
            f"{'用户' if msg.role == 'user' else 'AI'}: {msg.content}"
            for msg in messages
        ])
        
        try:
            from langchain_core.messages import HumanMessage
            
            response = await self.llm_client.ainvoke([
                HumanMessage(content=f"""请将以下对话总结为简洁的摘要，保留关键信息：

{conversation_text}

摘要格式：
- 主要话题：...
- 用户情绪：...
- 关键信息：...""")
            ])
            
            return response.content
            
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return ""
    
    async def get_recent_conversations(
        self,
        user_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取用户最近的会话列表"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
        )
        conversations = result.scalars().all()
        
        return [
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            }
            for conv in conversations
        ]
    
    async def delete_conversation(
        self,
        user_id: int,
        conversation_id: int
    ) -> bool:
        """删除会话及其所有消息"""
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            )
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            await self.db.delete(conversation)
            await self.db.commit()
            return True
        return False
