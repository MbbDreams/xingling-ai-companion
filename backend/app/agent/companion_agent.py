"""
AI 伴侣 Agent - 核心对话引擎（重构版）

使用分层记忆架构：
- CoreMemory: 核心记忆（常驻上下文）
- WorkingMemory: 工作记忆（对话历史 + 摘要）
- LongTermMemory: 长期记忆（向量检索）

参考：MemGPT/Letta、LangGraph、星野
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select

from .memory import (
    Embedder,
    CoreMemoryManager,
    WorkingMemoryManager,
    LongTermMemoryManager,
    MemoryExtractor,
    MemoryMaintenance,
)
from .context_builder import ContextBuilder
from .models import RelationshipType
from ..models import Companion, User
from ..core.config import settings


class CompanionAgent:
    """
    AI 伴侣 Agent（重构版）
    
    核心功能：
    1. 分层记忆管理（核心/工作/长期）
    2. 智能上下文组装（Token 预算控制）
    3. 异步记忆提取（不阻塞响应）
    4. 对话摘要（长对话压缩）
    """
    
    def __init__(
        self,
        db: AsyncSession,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
    ):
        self.db = db
        
        # LLM 配置
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model or "deepseek-chat"
        self.base_url = base_url or settings.openai_base_url or "https://api.deepseek.com"
        
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.8,
        )
        
        # 初始化分层记忆系统
        self.embedder = Embedder()
        self.core_memory_mgr = CoreMemoryManager(db, self.llm)
        self.working_memory_mgr = WorkingMemoryManager(db, self.llm)
        self.long_term_memory_mgr = LongTermMemoryManager(db, self.embedder)
        self.memory_extractor = MemoryExtractor(self.llm, self.long_term_memory_mgr)
        
        # 上下文组装器
        self.context_builder = ContextBuilder(
            session=db,
            core_memory_mgr=self.core_memory_mgr,
            working_memory_mgr=self.working_memory_mgr,
            long_term_memory_mgr=self.long_term_memory_mgr,
            llm=self.llm,
        )
        
        # 记忆维护器
        self.memory_maintenance = MemoryMaintenance(db, self.embedder)
    
    async def chat(
        self,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        核心对话方法（重构版）
        
        流程：
        1. 获取/创建会话
        2. 获取 companion_id
        3. 确保核心记忆已初始化
        4. 通过 ContextBuilder 组装完整上下文
        5. 调用 LLM 生成回复
        6. 存储消息到 messages 表
        7. 异步触发记忆提取（不阻塞响应）
        8. 检查是否需要生成对话摘要
        9. 返回结果
        """
        # 1. 获取或创建会话
        conversation = await self._get_or_create_conversation(user_id, conversation_id)
        conv_id = conversation.id
        
        # 2. 获取 companion_id
        companion_id = conversation.companion_id
        if not companion_id:
            # 获取用户的默认伴侣
            companion = await self._get_or_create_companion(user_id)
            companion_id = companion.id
        
        # 3. 确保核心记忆已初始化
        await self.core_memory_mgr.initialize(user_id, companion_id)
        
        # 4. 组装完整上下文
        messages = await self.context_builder.build_context(
            user_id=user_id,
            companion_id=companion_id,
            conversation_id=conv_id,
            user_message=message,
        )
        
        # 5. 调用 LLM
        response = await self.llm.ainvoke(messages)
        ai_message = response.content
        
        # 6. 存储对话
        await self._add_message(conv_id, "user", message)
        await self._add_message(conv_id, "assistant", ai_message)
        
        # 7. 异步触发记忆提取（不阻塞响应）
        asyncio.create_task(
            self._async_memory_tasks(
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conv_id,
                user_message=message,
                ai_response=ai_message,
            )
        )
        
        # 8. 返回结果
        return {
            "response": ai_message,
            "conversation_id": conv_id,
            "memories_used": [],  # 可从 context_builder 获取
        }
    
    async def chat_stream(
        self,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式对话方法
        
        逐步返回 AI 回复，提升用户体验
        """
        # 1. 获取或创建会话
        conversation = await self._get_or_create_conversation(user_id, conversation_id)
        conv_id = conversation.id
        
        # 2. 获取 companion_id
        companion_id = conversation.companion_id
        if not companion_id:
            companion = await self._get_or_create_companion(user_id)
            companion_id = companion.id
        
        # 3. 确保核心记忆已初始化
        await self.core_memory_mgr.initialize(user_id, companion_id)
        
        # 4. 组装完整上下文
        messages = await self.context_builder.build_context(
            user_id=user_id,
            companion_id=companion_id,
            conversation_id=conv_id,
            user_message=message,
        )
        
        # 5. 流式调用 LLM
        full_response = ""
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            full_response += content
            yield content
        
        # 6. 存储对话
        await self._add_message(conv_id, "user", message)
        await self._add_message(conv_id, "assistant", full_response)
        
        # 7. 异步触发记忆提取
        asyncio.create_task(
            self._async_memory_tasks(
                user_id=user_id,
                companion_id=companion_id,
                conversation_id=conv_id,
                user_message=message,
                ai_response=full_response,
            )
        )
    
    async def _get_or_create_conversation(
        self,
        user_id: int,
        conversation_id: Optional[int]
    ):
        """获取或创建会话"""
        from ..models import Conversation
        
        if conversation_id:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation
        
        # 获取或创建伴侣
        companion = await self._get_or_create_companion(user_id)
        
        # 创建新会话
        conversation = Conversation(
            user_id=user_id,
            companion_id=companion.id,
            title="新的聊天",
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def _get_or_create_companion(self, user_id: int):
        """获取或创建伴侣"""
        result = await self.db.execute(
            select(Companion).where(Companion.user_id == user_id)
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            companion = Companion(
                user_id=user_id,
                name="晚星",
                persona="温柔体贴的AI伴侣",
            )
            self.db.add(companion)
            await self.db.commit()
            await self.db.refresh(companion)
        
        return companion
    
    async def _add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> None:
        """添加消息到数据库"""
        from ..models import Message
        
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.db.add(message)
        await self.db.commit()
    
    async def _async_memory_tasks(
        self,
        user_id: int,
        companion_id: int,
        conversation_id: int,
        user_message: str,
        ai_response: str,
    ) -> None:
        """
        异步记忆任务（不阻塞用户响应）
        
        使用独立的数据库会话，避免与主会话冲突
        """
        # 创建独立的数据库会话
        from sqlalchemy.ext.asyncio import async_sessionmaker
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        try:
            async with async_session() as session:
                # 创建独立的记忆管理器
                embedder = Embedder()
                long_term_memory = LongTermMemoryManager(session, embedder)
                core_memory = CoreMemoryManager(session, self.llm)
                working_memory = WorkingMemoryManager(session, self.llm)
                memory_extractor = MemoryExtractor(self.llm, long_term_memory)
                
                # 1. 记忆提取
                await memory_extractor.extract_from_conversation(
                    user_message=user_message,
                    ai_response=ai_response,
                    user_id=user_id,
                    companion_id=companion_id,
                )
                
                # 2. 检查是否需要更新核心记忆
                user_memories = await long_term_memory.get_user_summary(user_id)
                if user_memories:
                    await core_memory.update_human_block(
                        user_id=user_id,
                        companion_id=companion_id,
                        memories_text=user_memories,
                    )
                
                # 3. 检查是否需要生成对话摘要
                await working_memory.maybe_summarize(
                    conversation_id=conversation_id,
                    user_id=user_id,
                )
                
                # 4. 更新关系状态
                await core_memory.update_relationship_block(
                    user_id=user_id,
                    companion_id=companion_id,
                )
                
                # 提交事务
                await session.commit()
                
        except Exception as e:
            print(f"[CompanionAgent] 异步记忆任务失败: {e}")
        finally:
            await engine.dispose()
    
    async def get_conversation_history(
        self,
        user_id: int,
        conversation_id: int
    ) -> List[Dict[str, str]]:
        """获取对话历史"""
        messages = await self.working_memory_mgr._get_recent_messages(
            conversation_id=conversation_id,
            limit=50,
        )
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    async def get_user_memories(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[str]:
        """获取用户记忆列表"""
        memories = await self.long_term_memory_mgr.retrieve_memories(
            user_id=user_id,
            query="",
            limit=limit,
        )
        return [m.content for m in memories]
    
    async def run_memory_maintenance(self) -> Dict[str, int]:
        """
        运行记忆维护任务
        
        建议通过后台任务定期调用
        
        Returns:
            清理统计
        """
        return await self.memory_maintenance.daily_cleanup()
