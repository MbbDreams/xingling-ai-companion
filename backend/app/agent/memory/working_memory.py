"""
工作记忆管理器 - Working Memory Manager

管理当前对话的短期上下文，采用滑动窗口 + 摘要的混合策略。
参考 LangGraph 的 SummarizationMiddleware 设计。

策略：
1. 保留最近 K 轮原始对话（滑动窗口）
2. 对更早的对话生成摘要
3. 当消息数超过阈值时自动触发摘要
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models import Message


class ConversationSummary(BaseModel):
    """对话摘要"""
    id: int
    conversation_id: int
    summary: str
    message_range: dict  # {"start_id": 1, "end_id": 15, "count": 15}
    created_at: datetime
    is_active: bool = True


class WorkingMemoryManager:
    """工作记忆管理器"""
    
    # 配置参数
    SUMMARY_THRESHOLD = 12      # 消息数超过此值时触发摘要
    KEEP_RECENT_MESSAGES = 6    # 滑动窗口保留最近 N 轮（用户+AI 算 1 轮）
    MAX_SUMMARY_TOKENS = 300    # 摘要最大 token 数
    
    def __init__(self, session: AsyncSession, llm=None):
        """
        初始化工作记忆管理器
        
        Args:
            session: 数据库会话
            llm: LLM 实例（用于生成摘要）
        """
        self.session = session
        self.llm = llm
    
    async def get_context_messages(
        self,
        conversation_id: int,
        user_message: str,
    ) -> list[dict]:
        """
        获取工作记忆上下文
        
        策略：
        1. 检查是否有活跃摘要 → 有则作为上下文开头
        2. 获取最近 KEEP_RECENT_MESSAGES 轮消息 → 作为上下文尾部
        3. 拼接为完整的消息列表
        
        Args:
            conversation_id: 会话 ID
            user_message: 当前用户消息
            
        Returns:
            消息列表 [{"role": "user/assistant", "content": "..."}]
        """
        messages = []
        
        # 1. 获取活跃摘要
        summary = await self.get_active_summary(conversation_id)
        if summary:
            messages.append({
                "role": "system",
                "content": f"[之前的对话摘要]\n{summary.summary}"
            })
        
        # 2. 获取最近消息（滑动窗口）
        recent_messages = await self._get_recent_messages(
            conversation_id, 
            limit=self.KEEP_RECENT_MESSAGES * 2  # 每轮包含 user + assistant
        )
        
        # 3. 转换为 LLM 格式
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    async def maybe_summarize(self, conversation_id: int, user_id: int) -> bool:
        """
        检查是否需要生成摘要，需要则生成
        
        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID
            
        Returns:
            是否生成了新摘要
        """
        # 获取当前消息数
        count_result = await self.session.execute(
            text("SELECT COUNT(*) FROM messages WHERE conversation_id = :cid"),
            {"cid": conversation_id}
        )
        total_count = count_result.scalar() or 0
        
        # 检查是否已有活跃摘要
        existing_summary = await self.get_active_summary(conversation_id)
        
        # 判断是否需要摘要
        if total_count <= self.SUMMARY_THRESHOLD:
            return False
        
        if existing_summary:
            # 已有摘要，检查是否需要更新
            covered_count = existing_summary.message_range.get("count", 0)
            if total_count - covered_count < self.SUMMARY_THRESHOLD:
                return False
        
        # 生成新摘要
        await self._generate_summary(conversation_id, user_id)
        return True
    
    async def get_active_summary(self, conversation_id: int) -> Optional[ConversationSummary]:
        """
        获取当前活跃摘要
        
        Args:
            conversation_id: 会话 ID
            
        Returns:
            摘要对象，不存在则返回 None
        """
        try:
            result = await self.session.execute(
                text("""
                    SELECT id, conversation_id, summary, message_range, created_at, is_active
                    FROM conversation_summaries
                    WHERE conversation_id = :cid AND is_active = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"cid": conversation_id}
            )
            row = result.fetchone()
            
            if row:
                return ConversationSummary(
                    id=row[0],
                    conversation_id=row[1],
                    summary=row[2],
                    message_range=row[3] or {},
                    created_at=row[4],
                    is_active=row[5],
                )
            return None
        except Exception as e:
            print(f"[WorkingMemory] 获取摘要失败: {e}")
            return None
    
    async def _get_recent_messages(
        self,
        conversation_id: int,
        limit: int = 12,
    ) -> list[Message]:
        """
        获取最近的消息（修复原版 bug：使用 offset 获取最新的消息）
        
        Args:
            conversation_id: 会话 ID
            limit: 消息数量限制
            
        Returns:
            消息列表（按时间正序）
        """
        # 先获取总数
        count_result = await self.session.execute(
            text("SELECT COUNT(*) FROM messages WHERE conversation_id = :cid"),
            {"cid": conversation_id}
        )
        total = count_result.scalar() or 0
        
        # 计算偏移量：跳过早期的消息，只取最近的
        offset = max(0, total - limit)
        
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .offset(offset)
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def _generate_summary(self, conversation_id: int, user_id: int) -> Optional[str]:
        """
        生成对话摘要
        
        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID
            
        Returns:
            生成的摘要文本
        """
        if not self.llm:
            return None
        
        try:
            # 获取需要摘要的消息（排除最近 KEEP_RECENT_MESSAGES 轮）
            count_result = await self.session.execute(
                text("SELECT COUNT(*) FROM messages WHERE conversation_id = :cid"),
                {"cid": conversation_id}
            )
            total = count_result.scalar() or 0
            
            # 只摘要早期消息
            summary_limit = max(0, total - self.KEEP_RECENT_MESSAGES * 2)
            
            if summary_limit <= 0:
                return None
            
            result = await self.session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(summary_limit)
            )
            messages = list(result.scalars().all())
            
            if not messages:
                return None
            
            # 构建对话文本
            conversation_text = "\n".join([
                f"{'用户' if m.role == 'user' else 'AI'}: {m.content}"
                for m in messages
            ])
            
            # 调用 LLM 生成摘要
            from langchain_core.messages import HumanMessage, SystemMessage
            
            summary_messages = [
                SystemMessage(content="""你是一个对话摘要助手。请将以下对话内容压缩为简洁的摘要。

要求：
1. 保留：主要话题、用户情绪、关键事实、用户偏好
2. 省略：寒暄、重复确认、过渡语句
3. 使用第三人称描述用户
4. 控制在100字以内

输出格式：直接输出摘要文本，不要加任何前缀。"""),
                HumanMessage(content=f"对话内容：\n{conversation_text}"),
            ]
            
            response = await self.llm.ainvoke(summary_messages)
            summary_text = response.content.strip()
            
            # 将旧摘要标记为非活跃
            await self.session.execute(
                text("""
                    UPDATE conversation_summaries 
                    SET is_active = FALSE 
                    WHERE conversation_id = :cid
                """),
                {"cid": conversation_id}
            )
            
            # 存储新摘要
            await self.session.execute(
                text("""
                    INSERT INTO conversation_summaries 
                        (conversation_id, user_id, summary, message_range, created_at, is_active)
                    VALUES 
                        (:cid, :uid, :summary, :range, NOW(), TRUE)
                """),
                {
                    "cid": conversation_id,
                    "uid": user_id,
                    "summary": summary_text,
                    "range": f'{{"start_id": {messages[0].id}, "end_id": {messages[-1].id}, "count": {len(messages)}}}',
                }
            )
            
            await self.session.commit()
            
            return summary_text
            
        except Exception as e:
            print(f"[WorkingMemory] 生成摘要失败: {e}")
            return None
