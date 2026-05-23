"""
上下文组装器 - Context Builder

按 Token 预算组装完整的 LLM 输入。
统一管理核心记忆、工作记忆、检索记忆的组装。

Token 预算分配（适配 DeepSeek 的 8K-32K 上下文窗口）：
- System Prompt (核心记忆): ~500 tokens
- 对话摘要: ~300 tokens
- 最近对话 (滑动窗口): ~1200 tokens
- 检索记忆: ~400 tokens
- 当前消息: ~200 tokens
- AI 回复预留: ~800 tokens
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory.core_memory import CoreMemoryManager
from app.agent.memory.working_memory import WorkingMemoryManager
from app.agent.memory.long_term_memory import LongTermMemoryManager
from app.agent.prompts import PromptBuilder
from app.agent.models import RelationshipType


class ContextBuilder:
    """上下文组装器"""
    
    # Token 预算
    BUDGET = {
        'system_prompt': 500,
        'summary': 300,
        'recent_messages': 1200,
        'retrieved_memories': 400,
        'current_message': 200,
        'ai_response': 800,
    }
    
    def __init__(
        self,
        session: AsyncSession,
        core_memory_mgr: CoreMemoryManager,
        working_memory_mgr: WorkingMemoryManager,
        long_term_memory_mgr: LongTermMemoryManager,
        llm=None,
    ):
        """
        初始化上下文组装器
        
        Args:
            session: 数据库会话
            core_memory_mgr: 核心记忆管理器
            working_memory_mgr: 工作记忆管理器
            long_term_memory_mgr: 长期记忆管理器
            llm: LLM 实例
        """
        self.session = session
        self.core_memory_mgr = core_memory_mgr
        self.working_memory_mgr = working_memory_mgr
        self.long_term_memory_mgr = long_term_memory_mgr
        self.llm = llm
    
    async def build_context(
        self,
        user_id: int,
        companion_id: int,
        conversation_id: int,
        user_message: str,
    ) -> list[dict]:
        """
        组装完整的 LLM 消息列表
        
        步骤：
        1. 获取核心记忆 → 构建 system prompt
        2. 获取工作记忆 → 摘要 + 最近对话
        3. 获取检索记忆 → 向量检索相关记忆
        4. 按 Token 预算裁剪
        5. 组装为消息列表
        
        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            conversation_id: 会话 ID
            user_message: 当前用户消息
            
        Returns:
            消息列表 [{"role": "system/user/assistant", "content": "..."}]
        """
        messages = []
        
        # 1. 构建系统提示（核心记忆）
        system_prompt = await self._build_system_prompt(
            user_id=user_id,
            companion_id=companion_id,
        )
        messages.append({"role": "system", "content": system_prompt})
        
        # 2. 获取工作记忆（摘要 + 最近对话）
        working_messages = await self.working_memory_mgr.get_context_messages(
            conversation_id=conversation_id,
            user_message=user_message,
        )
        messages.extend(working_messages)
        
        # 3. 获取检索记忆
        retrieved_memories = await self.long_term_memory_mgr.retrieve_memories(
            user_id=user_id,
            query=user_message,
            limit=5,
        )
        
        if retrieved_memories:
            memory_text = "\n".join([
                f"- {m.content}"
                for m in retrieved_memories[:5]
            ])
            messages.append({
                "role": "system",
                "content": f"[相关记忆]\n{memory_text}"
            })
        
        # 4. 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def _build_system_prompt(
        self,
        user_id: int,
        companion_id: int,
    ) -> str:
        """
        构建系统提示
        
        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            
        Returns:
            系统提示文本
        """
        # 获取核心记忆
        core_memory = await self.core_memory_mgr.get_core_memory(user_id, companion_id)
        
        # 获取 Companion 和 User 信息（使用 joinedload 避免懒加载问题）
        from app.models import Companion, User
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        
        result = await self.session.execute(
            select(Companion)
            .options(joinedload(Companion.user))
            .where(Companion.id == companion_id)
        )
        companion = result.scalar_one_or_none()
        
        # 使用 PromptBuilder 构建系统提示
        user_name = "用户"
        if companion and companion.user:
            user_name = companion.user.nickname or "用户"
        
        intimacy = companion.intimacy if companion else 0
        mood = companion.mood if companion else "calm"
        
        # 计算相识天数
        from datetime import datetime, timezone
        days_together = 1
        if companion:
            # 确保两个时间都有时区信息
            now = datetime.now(timezone.utc)
            created_at = companion.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            days_together = (now - created_at).days + 1
        
        # 构建情绪状态对象
        from .models import EmotionState
        emotion_state = EmotionState(
            primary_emotion=mood,
            intensity=5,
        )
        
        system_prompt = PromptBuilder.build_system_prompt(
            user_name=user_name,
            relationship_type=RelationshipType.PARTNER,
            relationship_level=intimacy // 100,
            intimacy=intimacy,
            current_emotion=emotion_state,
            memories=core_memory.human_block,
            conversation_turns=0,
        )
        
        # 追加核心记忆
        core_prompt = self.core_memory_mgr.build_core_prompt(core_memory)
        if core_prompt:
            system_prompt += f"\n\n{core_prompt}"
        
        # 添加相识天数
        system_prompt += f"\n\n我们相识已经{days_together}天了。"
        
        return system_prompt
    
    def estimate_tokens(self, messages: list[dict]) -> int:
        """
        估算消息列表的 token 数
        
        简单估算：中文约 1.5 字/token，英文约 4 字/token
        
        Args:
            messages: 消息列表
            
        Returns:
            估算的 token 数
        """
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            total_chars += len(content)
        
        # 简单估算
        return int(total_chars / 1.5)
    
    def trim_messages(self, messages: list[dict], max_tokens: int = 3000) -> list[dict]:
        """
        按 Token 预算裁剪消息
        
        策略：
        1. 保留第一条 system 消息
        2. 保留最后几轮对话
        3. 中间的消息按重要性裁剪
        
        Args:
            messages: 消息列表
            max_tokens: 最大 token 数
            
        Returns:
            裁剪后的消息列表
        """
        if self.estimate_tokens(messages) <= max_tokens:
            return messages
        
        # 分离 system 消息和对话消息
        system_messages = []
        conversation_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_messages.append(msg)
            else:
                conversation_messages.append(msg)
        
        # 从对话消息末尾开始保留
        trimmed_conversation = []
        current_tokens = self.estimate_tokens(system_messages)
        
        for msg in reversed(conversation_messages):
            msg_tokens = len(msg.get("content", "")) // 2
            if current_tokens + msg_tokens <= max_tokens:
                trimmed_conversation.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        return system_messages + trimmed_conversation
