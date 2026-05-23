"""
长期记忆管理器 - Long Term Memory Manager

管理跨会话的长期记忆，基于向量语义检索。
使用 pgvector 进行向量相似度搜索。

核心功能：
1. 存储记忆 + 生成向量嵌入
2. 语义检索相关记忆
3. 去重合并相似记忆
4. 时间衰减和重要性加权
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models import Memory
from app.agent.memory.embedder import Embedder, get_embedder
from app.agent.models import MemoryType


class MemoryEntry(BaseModel):
    """记忆条目"""
    id: int
    user_id: int
    content: str
    memory_type: str
    importance: float
    source: str
    created_at: datetime
    recall_count: int = 0


class LongTermMemoryManager:
    """长期记忆管理器"""
    
    # 配置参数
    MAX_RETRIEVE = 5              # 最大检索条数
    MIN_SIMILARITY = 0.6          # 最低相似度阈值
    TIME_DECAY_DAYS = 60          # 时间衰减天数
    RECENT_BOOST_DAYS = 7         # 最近记忆加权天数
    DEDUP_THRESHOLD = 0.85        # 去重相似度阈值
    
    # 检索权重
    WEIGHT_SIMILARITY = 0.6
    WEIGHT_IMPORTANCE = 0.2
    WEIGHT_RECENCY = 0.2
    
    def __init__(self, session: AsyncSession, embedder: Optional[Embedder] = None):
        """
        初始化长期记忆管理器
        
        Args:
            session: 数据库会话
            embedder: 向量化服务实例
        """
        self.session = session
        self.embedder = embedder or get_embedder()
    
    async def store_memory(
        self,
        user_id: int,
        companion_id: int,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
        source: str = "user_told",
        source_message_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        存储一条记忆
        
        Args:
            user_id: 用户 ID
            companion_id: 伴侣 ID
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性 (0-1)
            source: 来源 (user_told / ai_inferred)
            source_message_id: 来源消息 ID
            
        Returns:
            记忆 ID，失败返回 None
        """
        if not content or not content.strip():
            return None
        
        # 生成向量嵌入
        embedding = await self.embedder.embed_text(content)
        
        try:
            # 检查是否需要去重合并
            if embedding:
                merged = await self._check_and_merge(
                    user_id=user_id,
                    new_content=content,
                    new_embedding=embedding,
                    new_importance=importance,
                )
                if merged:
                    return None  # 已合并，不创建新记录
            
            # 插入新记忆
            result = await self.session.execute(
                text("""
                    INSERT INTO memories 
                        (user_id, companion_id, source_message_id, memory, category, 
                         importance, embedding, memory_type, source, created_at)
                    VALUES 
                        (:user_id, :companion_id, :source_message_id, :memory, :category,
                         :importance, :embedding::vector, :memory_type, :source, NOW())
                    RETURNING id
                """),
                {
                    "user_id": user_id,
                    "companion_id": companion_id,
                    "source_message_id": source_message_id,
                    "memory": content.strip(),
                    "category": memory_type,
                    "importance": importance,
                    "embedding": str(embedding) if embedding else None,
                    "memory_type": memory_type,
                    "source": source,
                }
            )
            
            memory_id = result.scalar()
            await self.session.commit()
            
            return memory_id
            
        except Exception as e:
            print(f"[LongTermMemory] 存储记忆失败: {e}")
            return None
    
    async def retrieve_memories(
        self,
        user_id: int,
        query: str,
        limit: int = 5,
        exclude_types: Optional[list[str]] = None,
    ) -> list[MemoryEntry]:
        """
        语义检索相关记忆
        
        检索流程：
        1. 将 query 生成 embedding 向量
        2. 在 memories 表中做向量相似度搜索（pgvector）
        3. 混合排序 = 语义相似度 * 0.6 + 重要性 * 0.2 + 时间新鲜度 * 0.2
        4. 过滤低于 MIN_SIMILARITY 的结果
        5. 返回 top limit 条
        
        Args:
            user_id: 用户 ID
            query: 查询文本
            limit: 返回数量限制
            exclude_types: 排除的记忆类型
            
        Returns:
            记忆条目列表
        """
        if not query or not query.strip():
            # 无查询文本，返回最重要的记忆
            return await self._get_top_memories(user_id, limit)
        
        # 生成查询向量
        query_embedding = await self.embedder.embed_text(query)
        
        if not query_embedding:
            # 向量化失败，回退到关键词检索
            return await self._keyword_search(user_id, query, limit)
        
        try:
            # 向量相似度搜索
            result = await self.session.execute(
                text("""
                    SELECT id, user_id, memory, category, importance, source, 
                           created_at, recall_count,
                           1 - (embedding <=> :query_embedding::vector) AS similarity
                    FROM memories
                    WHERE user_id = :user_id
                      AND embedding IS NOT NULL
                      AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT :limit * 2
                """),
                {
                    "user_id": user_id,
                    "query_embedding": str(query_embedding),
                    "limit": limit,
                }
            )
            
            rows = result.fetchall()
            
            # 计算综合得分并排序
            scored_memories = []
            for row in rows:
                memory_id, uid, content, category, importance, source, created_at, recall_count, similarity = row
                
                # 时间新鲜度得分
                recency_score = self._calculate_recency_score(created_at)
                
                # 综合得分
                final_score = (
                    similarity * self.WEIGHT_SIMILARITY +
                    importance * self.WEIGHT_IMPORTANCE +
                    recency_score * self.WEIGHT_RECENCY
                )
                
                # 过滤低相似度
                if similarity < self.MIN_SIMILARITY:
                    continue
                
                # 过滤排除类型
                if exclude_types and category in exclude_types:
                    continue
                
                scored_memories.append((final_score, MemoryEntry(
                    id=memory_id,
                    user_id=uid,
                    content=content,
                    memory_type=category,
                    importance=importance,
                    source=source,
                    created_at=created_at,
                    recall_count=recall_count or 0,
                )))
            
            # 按综合得分排序
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            
            # 更新 recall_count
            for _, memory in scored_memories[:limit]:
                await self._update_recall_count(memory.id)
            
            return [m for _, m in scored_memories[:limit]]
            
        except Exception as e:
            print(f"[LongTermMemory] 向量检索失败: {e}")
            return await self._keyword_search(user_id, query, limit)
    
    async def get_user_memories_by_type(
        self,
        user_id: int,
        memory_type: str,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        """
        获取用户指定类型的记忆
        
        Args:
            user_id: 用户 ID
            memory_type: 记忆类型
            limit: 返回数量限制
            
        Returns:
            记忆条目列表
        """
        try:
            result = await self.session.execute(
                text("""
                    SELECT id, user_id, memory, category, importance, source, 
                           created_at, recall_count
                    FROM memories
                    WHERE user_id = :user_id 
                      AND (memory_type = :memory_type OR category = :memory_type)
                      AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY importance DESC, created_at DESC
                    LIMIT :limit
                """),
                {
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "limit": limit,
                }
            )
            
            rows = result.fetchall()
            
            return [
                MemoryEntry(
                    id=row[0],
                    user_id=row[1],
                    content=row[2],
                    memory_type=row[3],
                    importance=row[4],
                    source=row[5],
                    created_at=row[6],
                    recall_count=row[7] or 0,
                )
                for row in rows
            ]
            
        except Exception as e:
            print(f"[LongTermMemory] 获取类型记忆失败: {e}")
            return []
    
    async def get_user_summary(self, user_id: int) -> str:
        """
        获取用户画像摘要文本
        
        汇总 basic_info/preference 类型的记忆
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户画像文本
        """
        # 获取基本信息
        basic_infos = await self.get_user_memories_by_type(user_id, "basic_info", limit=10)
        preferences = await self.get_user_memories_by_type(user_id, "preference", limit=10)
        
        parts = []
        
        if basic_infos:
            parts.append("基本信息：" + "；".join([m.content for m in basic_infos[:5]]))
        
        if preferences:
            parts.append("偏好：" + "；".join([m.content for m in preferences[:5]]))
        
        return "\n".join(parts)
    
    def _calculate_recency_score(self, created_at: datetime) -> float:
        """
        计算时间新鲜度得分
        
        Args:
            created_at: 创建时间
            
        Returns:
            新鲜度得分 [0, 1]
        """
        # 处理时区
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        days_ago = (now - created_at).days
        
        if days_ago <= self.RECENT_BOOST_DAYS:
            return 1.0
        elif days_ago <= 30:
            return 0.8
        elif days_ago <= self.TIME_DECAY_DAYS:
            return 0.5
        else:
            return 0.3
    
    async def _check_and_merge(
        self,
        user_id: int,
        new_content: str,
        new_embedding: list[float],
        new_importance: float,
    ) -> bool:
        """
        检查是否需要合并到已有记忆
        
        Args:
            user_id: 用户 ID
            new_content: 新记忆内容
            new_embedding: 新记忆向量
            new_importance: 新记忆重要性
            
        Returns:
            是否已合并
        """
        try:
            # 查找相似记忆
            result = await self.session.execute(
                text("""
                    SELECT id, memory, importance, 
                           1 - (embedding <=> :embedding::vector) AS similarity
                    FROM memories
                    WHERE user_id = :user_id AND embedding IS NOT NULL
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT 1
                """),
                {
                    "user_id": user_id,
                    "embedding": str(new_embedding),
                }
            )
            
            row = result.fetchone()
            
            if not row:
                return False
            
            memory_id, old_content, old_importance, similarity = row
            
            if similarity < self.DEDUP_THRESHOLD:
                return False
            
            # 合并：保留更详细的内容，更新重要性
            merged_content = new_content if len(new_content) > len(old_content) else old_content
            merged_importance = max(old_importance, new_importance)
            
            await self.session.execute(
                text("""
                    UPDATE memories 
                    SET memory = :content, 
                        importance = :importance,
                        is_merged = TRUE,
                        updated_at = NOW()
                    WHERE id = :id
                """),
                {
                    "id": memory_id,
                    "content": merged_content,
                    "importance": merged_importance,
                }
            )
            
            await self.session.commit()
            return True
            
        except Exception as e:
            print(f"[LongTermMemory] 合并记忆失败: {e}")
            return False
    
    async def _update_recall_count(self, memory_id: int) -> None:
        """更新记忆的召回次数"""
        try:
            await self.session.execute(
                text("""
                    UPDATE memories 
                    SET recall_count = recall_count + 1,
                        last_recalled_at = NOW()
                    WHERE id = :id
                """),
                {"id": memory_id}
            )
        except Exception:
            pass
    
    async def _get_top_memories(self, user_id: int, limit: int) -> list[MemoryEntry]:
        """获取最重要的记忆（无查询时回退）"""
        try:
            result = await self.session.execute(
                text("""
                    SELECT id, user_id, memory, category, importance, source, 
                           created_at, recall_count
                    FROM memories
                    WHERE user_id = :user_id
                      AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY importance DESC, created_at DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit}
            )
            
            rows = result.fetchall()
            
            return [
                MemoryEntry(
                    id=row[0],
                    user_id=row[1],
                    content=row[2],
                    memory_type=row[3],
                    importance=row[4],
                    source=row[5],
                    created_at=row[6],
                    recall_count=row[7] or 0,
                )
                for row in rows
            ]
            
        except Exception as e:
            print(f"[LongTermMemory] 获取重要记忆失败: {e}")
            return []
    
    async def _keyword_search(
        self,
        user_id: int,
        query: str,
        limit: int,
    ) -> list[MemoryEntry]:
        """关键词检索（向量检索失败时的降级方案）"""
        try:
            # 简单的关键词匹配
            keywords = query.strip().split()
            if not keywords:
                return []
            
            # 构建 ILIKE 条件
            like_conditions = " OR ".join([
                f"memory ILIKE '%{kw}%'"
                for kw in keywords[:3]  # 最多 3 个关键词
            ])
            
            result = await self.session.execute(
                text(f"""
                    SELECT id, user_id, memory, category, importance, source, 
                           created_at, recall_count
                    FROM memories
                    WHERE user_id = :user_id
                      AND ({like_conditions})
                      AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY importance DESC, created_at DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit}
            )
            
            rows = result.fetchall()
            
            return [
                MemoryEntry(
                    id=row[0],
                    user_id=row[1],
                    content=row[2],
                    memory_type=row[3],
                    importance=row[4],
                    source=row[5],
                    created_at=row[6],
                    recall_count=row[7] or 0,
                )
                for row in rows
            ]
            
        except Exception as e:
            print(f"[LongTermMemory] 关键词检索失败: {e}")
            return []
