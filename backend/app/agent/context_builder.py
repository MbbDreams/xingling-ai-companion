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

优化点：
1. 从 Companion 模型动态读取关系类型，替代硬编码 RelationshipType.PARTNER
2. 记忆召回质量评估机制
3. 更精确的 token 估算与基于 token 的摘要触发策略
4. 记忆自然融入 system prompt + 时间感知
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.agent.memory.core_memory import CoreMemoryManager
from app.agent.memory.working_memory import WorkingMemoryManager
from app.agent.memory.long_term_memory import LongTermMemoryManager
from app.agent.prompts import PromptBuilder
from app.agent.models import RelationshipType, EmotionState

logger = logging.getLogger(__name__)


class RetrievalQualityRecord:
    """记忆检索质量记录"""

    __slots__ = ("query", "returned_count", "avg_similarity", "min_similarity", "timestamp")

    def __init__(
        self,
        query: str,
        returned_count: int,
        avg_similarity: float,
        min_similarity: float,
        timestamp: datetime,
    ):
        self.query = query
        self.returned_count = returned_count
        self.avg_similarity = avg_similarity
        self.min_similarity = min_similarity
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query[:50],
            "returned_count": self.returned_count,
            "avg_similarity": round(self.avg_similarity, 4),
            "min_similarity": round(self.min_similarity, 4),
            "timestamp": self.timestamp.isoformat(),
        }


class ContextBuilder:
    """上下文组装器"""

    # Token 预算
    BUDGET = {
        "system_prompt": 500,
        "summary": 300,
        "recent_messages": 1200,
        "retrieved_memories": 400,
        "current_message": 200,
        "ai_response": 800,
    }

    # 摘要触发阈值（基于 token 数）
    SUMMARIZE_TOKEN_THRESHOLD = 1800

    # 中文字符近似 token 比率
    _CJK_CHAR_RATIO = 1.5
    # 英文单词近似 token 比率
    _EN_WORD_RATIO = 1.3

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

        # 记忆检索质量记录（最近 N 条）
        self._retrieval_quality_history: list[RetrievalQualityRecord] = []
        self._MAX_QUALITY_HISTORY = 50

    # =========================================================================
    # 公开方法
    # =========================================================================

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
        1. 获取核心记忆 → 构建 system prompt（含时间感知）
        2. 获取检索记忆 → 自然融入 system prompt
        3. 获取工作记忆 → 摘要 + 最近对话
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

        # 1. 获取检索记忆（在构建 system prompt 之前，以便融入）
        retrieved_memories, similarity_scores = await self._retrieve_and_evaluate(
            user_id=user_id,
            query=user_message,
            limit=5,
        )

        # 2. 构建系统提示（核心记忆 + 检索记忆 + 时间感知）
        system_prompt = await self._build_system_prompt(
            user_id=user_id,
            companion_id=companion_id,
            retrieved_memories=retrieved_memories,
        )
        messages.append({"role": "system", "content": system_prompt})

        # 3. 获取工作记忆（摘要 + 最近对话）
        working_messages = await self.working_memory_mgr.get_context_messages(
            conversation_id=conversation_id,
            user_message=user_message,
        )
        messages.extend(working_messages)

        # 4. 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        return messages

    async def _build_system_prompt(
        self,
        user_id: int,
        companion_id: int,
        retrieved_memories: Optional[list] = None,
    ) -> str:
        """
        构建系统提示

        优化：
        - 从 Companion 模型动态读取关系类型
        - 将检索记忆自然融入 prompt
        - 添加当前时间信息

        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            retrieved_memories: 检索到的记忆列表（可选）

        Returns:
            系统提示文本
        """
        from app.models import Companion, User

        # 获取核心记忆
        core_memory = await self.core_memory_mgr.get_core_memory(user_id, companion_id)

        # 获取 Companion 和 User 信息（使用 joinedload 避免懒加载问题）
        result = await self.session.execute(
            select(Companion)
            .options(joinedload(Companion.user))
            .where(Companion.id == companion_id)
        )
        companion = result.scalar_one_or_none()

        # 提取用户信息
        user_name = "用户"
        if companion and companion.user:
            user_name = companion.user.nickname or "用户"

        intimacy = companion.intimacy if companion else 0
        mood = companion.mood if companion else "calm"

        # --- 优化 1: 从 Companion 模型动态推断关系类型 ---
        relationship_type = self._resolve_relationship_type(companion)

        # 计算相识天数
        days_together = 1
        if companion:
            now = datetime.now(timezone.utc)
            created_at = companion.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            days_together = (now - created_at).days + 1

        # 构建情绪状态对象
        emotion_state = EmotionState(
            primary_emotion=mood,
            intensity=5,
        )

        # 使用 PromptBuilder 构建系统提示
        system_prompt = PromptBuilder.build_system_prompt(
            user_name=user_name,
            relationship_type=relationship_type,
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

        # --- 优化 4a: 添加时间感知 ---
        time_info = self._build_time_context()
        if time_info:
            system_prompt += f"\n\n{time_info}"

        # --- 优化 4b: 将检索记忆自然融入 system prompt ---
        if retrieved_memories:
            memory_section = self._build_memory_context_section(retrieved_memories)
            if memory_section:
                system_prompt += f"\n\n{memory_section}"

        return system_prompt

    def estimate_tokens(self, messages: list[dict]) -> int:
        """
        估算消息列表的 token 数

        优化：区分中英文字符，使用更精确的比率估算

        Args:
            messages: 消息列表

        Returns:
            估算的 token 数
        """
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            total_tokens += self.estimate_message_tokens(content)
        return total_tokens

    def estimate_message_tokens(self, text: str) -> int:
        """
        估算单条文本的 token 数

        策略：
        - 统计 CJK 字符数，按 ~1.5 字/token 估算
        - 统计英文单词数，按 ~1.3 词/token 估算
        - 标点符号和数字按单独 token 计

        Args:
            text: 待估算的文本

        Returns:
            估算的 token 数
        """
        if not text:
            return 0

        # 匹配 CJK 字符
        cjk_chars = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]", text))
        # 匹配英文单词
        en_words = len(re.findall(r"[a-zA-Z]+", text))
        # 剩余字符（标点、数字、空白等）按每字符约 0.5 token
        remaining_chars = len(text) - cjk_chars - sum(len(w) for w in re.findall(r"[a-zA-Z]+", text))

        tokens = (
            cjk_chars / self._CJK_CHAR_RATIO
            + en_words / self._EN_WORD_RATIO
            + remaining_chars * 0.5
        )
        return int(tokens) + 1  # +1 保底

    def should_summarize(self, messages: list[dict]) -> bool:
        """
        判断当前对话上下文是否需要触发摘要

        基于 token 数判断，比固定消息数阈值更精确。

        Args:
            messages: 当前工作记忆中的消息列表（不含 system 消息）

        Returns:
            是否需要摘要
        """
        # 只统计对话消息的 token（排除 system 消息）
        conversation_tokens = sum(
            self.estimate_message_tokens(msg.get("content", ""))
            for msg in messages
            if msg.get("role") != "system"
        )
        return conversation_tokens >= self.SUMMARIZE_TOKEN_THRESHOLD

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
            msg_tokens = self.estimate_message_tokens(msg.get("content", ""))
            if current_tokens + msg_tokens <= max_tokens:
                trimmed_conversation.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break

        return system_messages + trimmed_conversation

    # =========================================================================
    # 记忆检索与质量评估
    # =========================================================================

    async def _retrieve_and_evaluate(
        self,
        user_id: int,
        query: str,
        limit: int = 5,
    ) -> tuple[list, list[float]]:
        """
        检索记忆并评估召回质量

        Args:
            user_id: 用户 ID
            query: 查询文本
            limit: 返回数量限制

        Returns:
            (记忆列表, 相似度分数列表)
        """
        retrieved_memories = await self.long_term_memory_mgr.retrieve_memories(
            user_id=user_id,
            query=query,
            limit=limit,
        )

        # 尝试获取相似度分数
        similarity_scores = await self._get_similarity_scores(
            user_id=user_id,
            query=query,
            memories=retrieved_memories,
        )

        # 记录检索质量
        self._evaluate_retrieval_quality(
            query=query,
            memories=retrieved_memories,
            similarity_scores=similarity_scores,
        )

        return retrieved_memories, similarity_scores

    async def _get_similarity_scores(
        self,
        user_id: int,
        query: str,
        memories: list,
    ) -> list[float]:
        """
        获取检索记忆的相似度分数

        通过重新计算 query embedding 与每条记忆 embedding 的余弦相似度。

        Args:
            user_id: 用户 ID
            query: 查询文本
            memories: 检索到的记忆列表

        Returns:
            相似度分数列表
        """
        if not memories or not query.strip():
            return []

        try:
            embedder = self.long_term_memory_mgr.embedder
            if not embedder:
                return []

            query_embedding = await embedder.embed_text(query)
            if not query_embedding:
                return []

            from sqlalchemy import text

            memory_ids = [m.id for m in memories]
            if not memory_ids:
                return []

            # 批量查询相似度 - 使用字符串拼接避免 asyncpg 参数绑定问题
            placeholders = ", ".join(f":id_{i}" for i in range(len(memory_ids)))
            params = {f"id_{i}": mid for i, mid in enumerate(memory_ids)}
            
            # 将向量转换为 PostgreSQL 向量字面量格式
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            result = await self.session.execute(
                text(f"""
                    SELECT id, 1 - (embedding <=> '{embedding_str}'::vector) AS similarity
                    FROM memories
                    WHERE id IN ({placeholders})
                      AND embedding IS NOT NULL
                """),
                params,
            )

            score_map = {row[0]: row[1] for row in result.fetchall()}

            # 按原始记忆顺序返回分数
            return [score_map.get(m.id, 0.0) for m in memories]

        except Exception as e:
            logger.warning("[ContextBuilder] 获取相似度分数失败: %s", e)
            return []

    def _evaluate_retrieval_quality(
        self,
        query: str,
        memories: list,
        similarity_scores: list[float],
    ) -> RetrievalQualityRecord:
        """
        评估记忆召回质量

        记录每次检索的 query、返回数量、相似度分数，用于后续分析。

        Args:
            query: 查询文本
            memories: 检索到的记忆列表
            similarity_scores: 相似度分数列表

        Returns:
            检索质量记录
        """
        count = len(memories)

        if similarity_scores and count > 0:
            avg_sim = sum(similarity_scores) / count
            min_sim = min(similarity_scores)
        else:
            avg_sim = 0.0
            min_sim = 0.0

        record = RetrievalQualityRecord(
            query=query,
            returned_count=count,
            avg_similarity=avg_sim,
            min_similarity=min_sim,
            timestamp=datetime.now(timezone.utc),
        )

        # 维护固定长度的历史记录
        self._retrieval_quality_history.append(record)
        if len(self._retrieval_quality_history) > self._MAX_QUALITY_HISTORY:
            self._retrieval_quality_history.pop(0)

        # 低质量检索告警
        if count > 0 and avg_sim < 0.65:
            logger.info(
                "[ContextBuilder] 低质量检索: query='%s', count=%d, avg_sim=%.3f",
                query[:50],
                count,
                avg_sim,
            )

        return record

    def get_retrieval_quality_stats(self) -> dict[str, Any]:
        """
        获取记忆检索质量统计

        Returns:
            统计信息字典
        """
        history = self._retrieval_quality_history
        if not history:
            return {"total_retrievals": 0}

        avg_counts = sum(r.returned_count for r in history) / len(history)
        avg_similarities = sum(r.avg_similarity for r in history) / len(history)
        min_similarities = min(r.min_similarity for r in history)

        return {
            "total_retrievals": len(history),
            "avg_returned_count": round(avg_counts, 2),
            "avg_similarity": round(avg_similarities, 4),
            "min_similarity_ever": round(min_similarities, 4),
            "recent_records": [r.to_dict() for r in history[-5:]],
        }

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    @staticmethod
    def _resolve_relationship_type(companion: Optional[Any]) -> RelationshipType:
        """
        从 Companion 模型动态推断关系类型

        根据 Companion 的 level 字符串推断关系类型：
        - Lv.1 ~ Lv.3  → FRIEND
        - Lv.4 ~ Lv.6  → PARTNER
        - Lv.7 ~ Lv.9  → SPOUSE
        - Lv.10+       → SPOUSE

        如果 Companion 为 None 或 level 无法解析，默认返回 FRIEND。

        Args:
            companion: Companion 实例

        Returns:
            关系类型枚举
        """
        if companion is None:
            return RelationshipType.FRIEND

        level_str = getattr(companion, "level", "") or ""
        # 从 "Lv.3" 格式中提取数字
        match = re.search(r"(\d+)", level_str)
        if not match:
            return RelationshipType.FRIEND

        level_num = int(match.group(1))

        if level_num <= 3:
            return RelationshipType.FRIEND
        elif level_num <= 6:
            return RelationshipType.PARTNER
        else:
            return RelationshipType.SPOUSE

    @staticmethod
    def _build_time_context() -> str:
        """
        构建时间感知上下文

        在 system prompt 中注入当前时间信息，帮助 AI 理解时间相关对话。

        Returns:
            时间上下文文本
        """
        now = datetime.now(timezone.utc)

        # 转换为东八区（中国标准时间）
        try:
            from zoneinfo import ZoneInfo
            cst = now.astimezone(ZoneInfo("Asia/Shanghai"))
        except Exception:
            # zoneinfo 不可用时，手动偏移 +8 小时
            from datetime import timedelta
            cst = now + timedelta(hours=8)

        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[cst.weekday()]

        time_context = (
            f"[当前时间] {cst.year}年{cst.month}月{cst.day}日 {weekday} "
            f"{cst.hour:02d}:{cst.minute:02d}"
        )

        # 根据时段添加提示
        hour = cst.hour
        if 0 <= hour < 6:
            time_context += "（深夜）"
        elif 6 <= hour < 9:
            time_context += "（早晨）"
        elif 9 <= hour < 12:
            time_context += "（上午）"
        elif 12 <= hour < 14:
            time_context += "（中午）"
        elif 14 <= hour < 18:
            time_context += "（下午）"
        elif 18 <= hour < 22:
            time_context += "（晚上）"
        else:
            time_context += "（夜晚）"

        return time_context

    @staticmethod
    def _build_memory_context_section(memories: list) -> str:
        """
        将检索到的记忆构建为自然融入 system prompt 的段落

        优化：不再是单独的 system 消息，而是作为 prompt 的一部分，
        引导 AI 在回复中自然引用相关记忆。

        Args:
            memories: 检索到的记忆列表

        Returns:
            记忆上下文段落文本
        """
        if not memories:
            return ""

        memory_lines = []
        for i, m in enumerate(memories[:5], 1):
            content = m.content if hasattr(m, "content") else str(m)
            memory_lines.append(f"{i}. {content}")

        section = (
            "## 与当前对话相关的记忆（严格限制）\n"
            "以下是从记忆系统中检索到的、与此刻对话相关的过往记忆：\n"
            + "\n".join(memory_lines)
            + "\n\n"
            "【极其重要】\n"
            "1. 你只能引用上面列出的确切内容\n"
            "2. 禁止推测、扩展、补充任何未列出的信息\n"
            "3. 如果上面只写'喜欢打篮球'，你不能说'想找队友'、'经常打'等\n"
            "4. 不确定时必须用问句：'我记得你好像说过...对吗？'\n"
            "5. 选择 1-2 条最相关的记忆，用关心或回忆的语气自然带出"
        )

        return section
