"""
记忆维护器 - Memory Maintenance

定期清理、合并、衰减记忆。
建议通过 FastAPI 后台任务或 APScheduler 调用。
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory.embedder import Embedder, get_embedder


class MemoryMaintenance:
    """记忆维护器"""
    
    # 配置参数
    CLEANUP_DAYS = 90            # 清理超过此天数的低价值记忆
    DECAY_DAYS = 60              # 重要性衰减天数
    DECAY_FACTOR = 0.8           # 衰减系数
    MIN_IMPORTANCE = 0.3         # 清理的最低重要性阈值
    MERGE_THRESHOLD = 0.9        # 合并相似度阈值
    
    # 不衰减的记忆类型（基本信息不会过时）
    NO_DECAY_TYPES = ['basic_info', 'family', 'pet']
    
    def __init__(
        self,
        session: AsyncSession,
        embedder: Optional[Embedder] = None,
    ):
        """
        初始化记忆维护器
        
        Args:
            session: 数据库会话
            embedder: 向量化服务
        """
        self.session = session
        self.embedder = embedder or get_embedder()
    
    async def daily_cleanup(self) -> dict:
        """
        每日清理任务
        
        执行内容：
        1. 清理过期记忆
        2. 重要性衰减
        3. 相似记忆合并
        
        Returns:
            清理统计 {"deleted": N, "decayed": N, "merged": N}
        """
        stats = {
            "deleted": 0,
            "decayed": 0,
            "merged": 0,
        }
        
        # 1. 清理过期记忆
        stats["deleted"] = await self._cleanup_expired()
        
        # 2. 重要性衰减
        stats["decayed"] = await self._decay_importance()
        
        # 3. 相似记忆合并
        stats["merged"] = await self._merge_similar()
        
        return stats
    
    async def update_core_memories(self) -> dict:
        """
        更新所有用户的核心记忆（用户画像 + 关系状态）
        
        Returns:
            更新统计 {"updated": N}
        """
        stats = {"updated": 0}
        
        try:
            # 获取所有用户
            result = await self.session.execute(
                text("SELECT DISTINCT user_id FROM core_memories")
            )
            user_ids = [row[0] for row in result.fetchall()]
            
            for user_id in user_ids:
                # 获取该用户的 companion_id
                companion_result = await self.session.execute(
                    text("""
                        SELECT companion_id FROM core_memories 
                        WHERE user_id = :user_id
                    """),
                    {"user_id": user_id}
                )
                companion_row = companion_result.fetchone()
                
                if companion_row:
                    await self._update_user_profile(user_id, companion_row[0])
                    stats["updated"] += 1
            
            await self.session.commit()
            
        except Exception as e:
            print(f"[MemoryMaintenance] 更新核心记忆失败: {e}")
        
        return stats
    
    async def _cleanup_expired(self) -> int:
        """清理过期记忆"""
        try:
            # 删除过期记忆 - 使用 f-string 避免 INTERVAL 内的参数绑定问题
            result = await self.session.execute(
                text(f"""
                    DELETE FROM memories
                    WHERE (expires_at IS NOT NULL AND expires_at < NOW())
                       OR (recall_count = 0 
                           AND created_at < NOW() - INTERVAL '{self.CLEANUP_DAYS} days'
                           AND importance < :min_importance)
                """),
                {"min_importance": self.MIN_IMPORTANCE}
            )
            
            deleted = result.rowcount
            await self.session.commit()
            
            return deleted
            
        except Exception as e:
            print(f"[MemoryMaintenance] 清理过期记忆失败: {e}")
            return 0
    
    async def _decay_importance(self) -> int:
        """重要性衰减"""
        try:
            # 对超过 DECAY_DAYS 的记忆进行衰减
            # 排除 basic_info 等不会过时的类型
            # 使用 f-string 避免 INTERVAL 内的参数绑定问题
            result = await self.session.execute(
                text(f"""
                    UPDATE memories
                    SET importance = importance * :factor
                    WHERE created_at < NOW() - INTERVAL '{self.DECAY_DAYS} days'
                      AND importance > 0.1
                      AND memory_type NOT IN ({','.join([f"'{t}'" for t in self.NO_DECAY_TYPES])})
                """),
                {"factor": self.DECAY_FACTOR}
            )
            
            decayed = result.rowcount
            await self.session.commit()
            
            return decayed
            
        except Exception as e:
            print(f"[MemoryMaintenance] 重要性衰减失败: {e}")
            return 0
    
    async def _merge_similar(self) -> int:
        """合并相似记忆"""
        try:
            # 获取所有用户
            result = await self.session.execute(
                text("SELECT DISTINCT user_id FROM memories")
            )
            user_ids = [row[0] for row in result.fetchall()]
            
            merged_count = 0
            
            for user_id in user_ids:
                merged_count += await self._merge_user_memories(user_id)
            
            return merged_count
            
        except Exception as e:
            print(f"[MemoryMaintenance] 合并相似记忆失败: {e}")
            return 0
    
    async def _merge_user_memories(self, user_id: int) -> int:
        """合并单个用户的相似记忆"""
        try:
            # 获取用户的记忆（按重要性排序，保留重要的）
            result = await self.session.execute(
                text("""
                    SELECT id, memory, embedding, importance
                    FROM memories
                    WHERE user_id = :user_id AND embedding IS NOT NULL
                    ORDER BY importance DESC
                    LIMIT 50
                """),
                {"user_id": user_id}
            )
            
            memories = result.fetchall()
            merged = 0
            to_delete = set()
            
            # 两两比较
            for i, (id_a, content_a, embedding_a, importance_a) in enumerate(memories):
                if id_a in to_delete:
                    continue
                
                for id_b, content_b, embedding_b, importance_b in memories[i+1:]:
                    if id_b in to_delete:
                        continue
                    
                    # 计算相似度
                    if embedding_a and embedding_b:
                        similarity = Embedder.cosine_similarity(
                            eval(embedding_a), eval(embedding_b)
                        )
                        
                        if similarity > self.MERGE_THRESHOLD:
                            # 合并：保留重要性更高的
                            if importance_a >= importance_b:
                                to_delete.add(id_b)
                            else:
                                to_delete.add(id_a)
                                break
                            merged += 1
            
            # 删除被合并的记忆
            if to_delete:
                await self.session.execute(
                    text(f"""
                        DELETE FROM memories WHERE id IN ({','.join(map(str, to_delete))})
                    """)
                )
                await self.session.commit()
            
            return merged
            
        except Exception as e:
            print(f"[MemoryMaintenance] 合并用户记忆失败: {e}")
            return 0
    
    async def _update_user_profile(self, user_id: int, companion_id: int) -> None:
        """更新用户画像"""
        try:
            # 获取用户的基本信息和偏好记忆
            result = await self.session.execute(
                text("""
                    SELECT memory FROM memories
                    WHERE user_id = :user_id 
                      AND memory_type IN ('basic_info', 'preference')
                    ORDER BY importance DESC
                    LIMIT 20
                """),
                {"user_id": user_id}
            )
            
            memories = [row[0] for row in result.fetchall()]
            
            if memories:
                # 生成用户画像文本
                profile_text = "；".join(memories[:10])
                
                # 更新 core_memory
                await self.session.execute(
                    text("""
                        UPDATE core_memories
                        SET human_block = :profile, last_updated_at = NOW()
                        WHERE user_id = :user_id AND companion_id = :companion_id
                    """),
                    {
                        "profile": profile_text,
                        "user_id": user_id,
                        "companion_id": companion_id,
                    }
                )
            
        except Exception as e:
            print(f"[MemoryMaintenance] 更新用户画像失败: {e}")
